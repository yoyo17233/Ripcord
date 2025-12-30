import asyncio, os, time, json, threading
from utils.utilities import dm_superuser
from utils.data import containers
from collections import defaultdict

VERBOSE = True

console_emptier = False
console_buffer = []
log_dict = defaultdict(list)

def poll_log_file(container_id, loop, bot):
    from utils.minecraft import build_log
    filepath = build_log(containers[container_id]["server"])
    last_position = os.path.getsize(filepath)
    while True:
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
                if(VERBOSE): print("newlines found in containerid " + str(container_id))
                line = line.strip()
                if line:
                    if(VERBOSE): print("line found = " + line)
                    asyncio.run_coroutine_threadsafe(
                        send_log_to_discord(container_id, line, bot),
                        loop
                    )

        except Exception as e:
            print(f"[ERROR] Log reader crashed: {e}")

        time.sleep(1)

async def send_log_to_discord(container_id, message, bot):
    usernames = get_usernames(container_id)

    if not message.strip():
        return
    
    # Console
    log_dict[container_id].append(message)
    print(f"Container {container_id} now has {len(log_dict[container_id])} messages.")

    from utils.minecraft import get_server_loader
    loader = get_server_loader(containers[container_id]["server"])

    
    if "<" in message and ">" in message and "[Rcon] <" not in message:
        if loader == "vanilla": # Vanilla
            newmessage = message[message.index('<')+1:]
        if loader == "neoforge": # Vanilla
            newmessage = message[message.index('[Server thread/INFO] [net.minecraft.server.MinecraftServer/]:') + 62:]
        if loader == "forge": # Vanilla
            newmessage = message[message.index('] [Server thread/INFO]: ') + 24:]

        if newmessage.startswith(tuple(usernames)):
            chatchannel = bot
            await chatchannel.send(f"```{message[message.index('<'):]}```")
            return


def get_usernames(container_id):
    from utils.minecraft import build_whitelist
    path = build_whitelist(containers[container_id]["server"])
    with open(path, "r") as f:
        data = json.load(f)
    usernames = [entry["name"] for entry in data]
    return usernames

async def start_log_buffer_task(self):
    print("started log buffer task...")
    while True:
        log_dict_copy = log_dict.copy()
        for container_id, messages in log_dict_copy.items():
            # Send the grouped messages to the appropriate channels
            console_channel = await self.bot.fetch_channel(containers[container_id]["console_id"])
            print("console emptier is running...")
            # Join the messages and send them to Discord (adjust size limit if needed)
            joined = "\n".join(messages)
            if len(joined) > 7600:
                await console_channel.send(f"```{joined[:1900]}```")
                await console_channel.send(f"```{joined[1900:3800]}```")
                await console_channel.send(f"```{joined[3800:5700]}```")
                await console_channel.send(f"```{joined[5700:7600]}```")
            elif len(joined) > 5700:
                await console_channel.send(f"```{joined[:1900]}```")
                await console_channel.send(f"```{joined[1900:3800]}```")
                await console_channel.send(f"```{joined[3800:5700]}```")
                await console_channel.send(f"```{joined[5700:]}```")
            elif len(joined) > 3800:
                await console_channel.send(f"```{joined[:1900]}```")
                await console_channel.send(f"```{joined[1900:3800]}```")
                await console_channel.send(f"```{joined[3800:]}```")
            elif len(joined) > 1900:
                await console_channel.send(f"```{joined[:1900]}```")
                await console_channel.send(f"```{joined[1900:]}```")
            else:
                await console_channel.send(f"```{joined}```")

        # Clear the log_dict after sending
        log_dict.clear()
        await asyncio.sleep(1)

async def startlogging(self, container_id):
    containers[container_id]["logging"] = True

    dm_superuser(self.bot, "a logging loop starting for container id " + str(container_id))
    
    threading.Thread(target=poll_log_file, args=(container_id, self.bot.loop, self.bot), daemon=True).start()
    if not console_emptier:
        dm_superuser(self.bot, "STARTING THE ONE CONSOLE EMPTIER TASK")
        console_emptier = True
        self.bot.loop.create_task(start_log_buffer_task(self))