import asyncio, os, json, threading, re
from utils.utilities import dm_superuser
from utils.data import containers, save_containers
from collections import defaultdict
from utils.minecraft_io import build_log, build_whitelist, get_server_loader

VERBOSE = True

console_emptier = False
console_emptier_task = None
log_dict = defaultdict(list)
active_logs = {}

# =========================
# THREAD FUNCTION
# =========================
def poll_log_file(container_id, loop, bot, stop_event):
    filepath = build_log(containers[container_id]["server"])
    last_position = os.path.getsize(filepath)

    while not stop_event.is_set():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()

                if file_size < last_position:
                    last_position = 0

                f.seek(last_position)
                new_lines = f.readlines()
                last_position = f.tell()

            for line in new_lines:
                if stop_event.is_set():
                    break

                line = line.strip()
                if line:
                    asyncio.run_coroutine_threadsafe(
                        handle_log_line(container_id, line, bot),
                        loop
                    )

        except Exception as e:
            print(f"[ERROR] Log reader crashed: {e}")

        # Better than time.sleep → instant shutdown
        stop_event.wait(1)

    print(f"[INFO] Thread for container {container_id} shutting down cleanly.")


# =========================
# DISCORD SENDER
# =========================
async def handle_log_line(container_id, message, bot):
    if not message.strip():
        return

    usernames = get_usernames(container_id)

    # Add log line to console buffer
    log_dict[container_id].append(message)

    if "[net.minecraft.server.MinecraftServer/]" not in message:
        return

    loader = get_server_loader(containers[container_id]["server"])

    index = "[net.minecraft.server.MinecraftServer/]: "

    valid_loaders = ["vanilla", "neoforge", "spigot"] # Currently implemented loaders

    if loader == "neoforge":
        neoforge_index = "[net.minecraft.server.MinecraftServer/]: "
        if neoforge_index not in message:
            return
        index = neoforge_index

    if loader == "vanilla":
        vanilla_index = "[Server thread/INFO]: "
        if vanilla_index not in message:
            return
        index = vanilla_index

    if loader == "spigot":
        spigot_index = "INFO]: "
        if spigot_index not in message:
            return
        index = spigot_index

    if loader not in valid_loaders: # Legacy handling, may not work
        print(f"unrecognized loader {loader}, using legacy log parsing (may not work)")
        # =========================
        # CHAT DETECTION
        # =========================
        if "<" in message and ">" in message and "[Rcon] <" not in message:
            chat_name = re.search(r'<([^>]*)>', message).group(1)
            for username in usernames:
                if username in chat_name:
                    chatchannel = await bot.fetch_channel(containers[container_id]["chat_id"])
                    await chatchannel.send(f"```{chat_name}: {message[message.index('> '):]}```")
                    return

        # =========================
        # OTHER USER EVENTS
        # =========================
        if loader == "vanilla":
            newmessage = message[message.index('<')+1:] if "<" in message else message
        elif loader in ["neoforge", "forge"]:
            newmessage = message.split("]:", 1)[-1].strip()
        else:
            return

        if newmessage.startswith(tuple(usernames)):
            chatchannel = await bot.fetch_channel(containers[container_id]["chat_id"])
            await chatchannel.send(f"```{newmessage}```")
        return

    raw_message = message.split(index, 1)[-1].strip()
    new_message = raw_message
    message_type = "none"

    # Player Message
    for username in usernames:
        if "<" in raw_message and ">" in raw_message:
            if username in raw_message[:raw_message.index(">")]:
                new_message = f"```{username}: {raw_message.split('>', 1)[-1].strip()}```"
                message_type = "message"
                break

    # Player Event
    if message_type == "none":
        for username in usernames:
            if username in raw_message:
                new_message = f"```{raw_message}```"
                message_type = "event"
                if "joined the game" in raw_message:
                    containers[container_id]["players"] = containers[container_id].get("players", []) + [username]
                    from utils.discord import refresh_panel
                    await refresh_panel(bot, container_id)
                    save_containers()
                if "left the game" in raw_message:
                    containers[container_id]["players"] = [player for player in containers[container_id]["players"] if player != username]
                    from utils.discord import refresh_panel
                    await refresh_panel(bot, container_id)
                    save_containers()
                if ":" in new_message: # Handles /list
                    return
                break

    if message_type != "none":
        chatchannel = await bot.fetch_channel(containers[container_id]["chat_id"])
        await chatchannel.send(new_message)

# =========================
# WHITELIST READER
# =========================
def get_usernames(container_id):
    path = build_whitelist(containers[container_id]["server"])
    with open(path, "r") as f:
        data = json.load(f)
    return [entry["name"] for entry in data]


# =========================
# CONSOLE BUFFER TASK
# =========================
async def start_log_buffer_task(bot):
    global console_emptier, console_emptier_task
    print("Started log buffer task...")

    try:
        while True:
            log_dict_copy = dict(log_dict)
            log_dict.clear()

            for container_id, messages in log_dict_copy.items():
                console_channel = await bot.fetch_channel(
                    containers[container_id]["console_id"]
                )

                joined = "\n".join(messages)

                # Discord message splitting
                for i in range(0, len(joined), 1900):
                    chunk = joined[i:i+1900]
                    await console_channel.send(f"```{chunk}```")

            await asyncio.sleep(1)
    finally:
        console_emptier = False
        console_emptier_task = None


# =========================
# START LOGGING
# =========================
async def startlogging(bot, container_id):
    global console_emptier, console_emptier_task, active_logs

    await dm_superuser(
        bot,
        f"ATTEMPTING TO START LOGGING FOR {containers[container_id]['nick']}"
    )

    # Already running?
    if container_id in active_logs:
        data = active_logs[container_id]
        if data["thread"].is_alive():
            await dm_superuser(bot, "SERVER ALREADY HAS LIVING THREAD")
            return

    stop_event = threading.Event()

    loop = asyncio.get_running_loop()

    log_thread = threading.Thread(
        target=poll_log_file,
        args=(container_id, loop, bot, stop_event),
        daemon=True
    )

    log_thread.start()

    active_logs[container_id] = {
        "thread": log_thread,
        "stop_event": stop_event
    }

    containers[container_id]["logging"] = True

    await dm_superuser(bot, f"Started logging for {containers[container_id]['nick']}")

    # Start buffer task once
    if not console_emptier or console_emptier_task is None or console_emptier_task.done():
        console_emptier = True
        console_emptier_task = loop.create_task(start_log_buffer_task(bot))


# =========================
# STOP LOGGING
# =========================
def stop_logging(container_id):
    if container_id not in active_logs:
        print(f"[INFO] No active thread for container {container_id}")
        return False

    data = active_logs[container_id]
    thread = data["thread"]
    stop_event = data["stop_event"]

    print(f"[INFO] Stopping thread for container {container_id}...")

    stop_event.set()
    thread.join(timeout=5)

    if thread.is_alive():
        print(f"[WARN] Thread did not stop in time.")
        return False

    del active_logs[container_id]
    containers[container_id]["logging"] = False

    print(f"[INFO] Thread stopped cleanly.")
    return True

def get_active_log_names():
    active = []

    for container_id, data in active_logs.items():
        thread = data.get("thread")

        if thread and thread.is_alive():
            name = containers[container_id].get("nick", str(container_id))
            active.append(name)

    return ", ".join(active) if active else "None"
