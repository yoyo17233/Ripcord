import os, asyncio, socket, time, discord
from pathlib import Path
from dotenv import load_dotenv
from discord.app_commands import CheckFailure
from utils.perms import check_console_perm_msg
from utils.data import containers, save_containers, get_containerid_from_channelid
from utils.networking import command, is_server_up
from utils.minecraft_io import build_run, read_server_properties, write_server_properties, generate_run_bat
from utils.polling import startlogging, active_logs, stop_logging
from utils.utilities import log

load_dotenv()

SERVER_PATH = os.getenv("SERVER_DIR")
SERVER_DIR = Path(SERVER_PATH)
LOG_LOCATION = os.getenv("LOG_LOCATION")
RUNFILE = os.getenv("RUNFILE")

POLLSECONDS = 3

VERBOSE = False

local_ip = socket.gethostbyname(socket.gethostname())
RCON_IP = local_ip
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

RUN_BAT_TEMPLATE = r'''@echo off
cd /d "%~dp0"

"C:\Program Files\Java\jdk-22\bin\java.exe" ^
  -Xms4G ^
  -Xmx10G ^
  -jar "{jar}" ^
  nogui

exit
'''
        
async def server_start_loop(bot, container_id):
    containers[container_id]["starting"] = True
    starttime = time.time()
    while containers[container_id]["starting"]:
        if time.time() - starttime > 300:
            containers[container_id]["starting"] = False
            save_containers()
            return
        if is_server_up(container_id):
            #log("server is up")
            containers[container_id]["up"] = True
            save_containers()
            if not containers[container_id]["logging"]:
                log(f"Starting logging for {containers[container_id]['server']} server in container {containers[container_id]['nick']}")
                await startlogging(bot, container_id)
            #log("serverstarting setting to 0...")
            containers[container_id]["starting"] = False
            save_containers()
            #log("serverstarting successfully set to 0")
            return
        await asyncio.sleep(POLLSECONDS)

async def startserver(bot, container_id):
    server_name = containers[container_id]["server"]

    server_props = read_server_properties(server_name)

    server_props["server-port"] = containers[container_id]["port"]
    server_props["white-list"] = True
    server_props["view-distance"] = 16
    server_props["simulation-distance"] = 16
    server_props["rcon.port"] = containers[container_id]["port"] + 10000
    server_props["rcon.password"] = RCON_PASSWORD
    server_props["enforce-whitelist"] = True
    server_props["enable-rcon"] = True
    server_props["allow-flight"] = True
    server_props["difficulty"] = "hard"
    additive = 'a'
    if server_name[0] in ['a','e','i','o','u']:
        additive = 'an'
    server_props["motd"] = f"{additive} {server_name} Minecraft Server"

    write_server_properties(server_name, server_props)

    runfilepath = SERVER_DIR / server_name / "run.bat"
    #log(f"checking for path {runfilepath}")
    if not os.path.exists(runfilepath):
        log("Generating run.bat")
        generate_run_bat(server_name)

    #log("starting " + containers[container_id]["server"] + " server")
    #log("running command: " + build_run(containers[container_id]["server"]))
    await asyncio.create_subprocess_shell(
        build_run(containers[container_id]["server"]),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    #log("started server process, now waiting for server to come up...")
    await server_start_loop(bot, container_id)
    return True

async def stopserver(container_id):
    container = containers[container_id]

    # Stop the Minecraft server
    command("stop", container_id)

    # Update state
    container["up"] = False
    container["logging"] = False
    container["players"] = []
    save_containers()

    # Stop logging thread (gracefully)
    if container_id in active_logs:
        #log(f"Stopping log thread for container {containers[container_id]['nick']}...")
        stopped = await asyncio.to_thread(stop_logging, container_id)

        if not stopped:
            log(f"Thread did not shut down cleanly for {containers[container_id]['nick']}", "WARN")
    else:
        log(f"No active log thread for container {containers[container_id]['nick']}")

async def checkserversup(bot):
    from utils.discord import refresh_panel, start_loop
    #log("Checking if any servers are down...")
    
    for container_id, container_data in containers.items():
        #log(f"Checking container {container_data['nick']} for crashes...")
        
        if not is_server_up(container_id) and containers[container_id]["up"]:
            await refresh_panel(bot, container_id)
            log(f"{containers[container_id]['server']} crashed in container {containers[container_id]['nick']}, restarting")
            
            channel_id = container_data["bot_channel_id"]
            botchannel = bot.get_channel(channel_id)
            while not botchannel:
                await asyncio.sleep(3)
                botchannel = bot.get_channel(channel_id)
            
            previousrevive = containers[container_id]["lastrevive"]
            if time.time() - previousrevive < 600:
                log("Two crashes within 10 minutes, catastrophic error")
                perm_id = containers[container_id]["bot_perm"]
                await botchannel.send(f"{containers[container_id]["server"]} server has crashed twice in 10 minutes. Please check in <@&{perm_id}>")
                containers[container_id]["up"] = False
                save_containers()
                continue
            msg = await botchannel.send(f"{containers[container_id]["server"]} server appears to be down. Restarting...")
            containers[container_id]["starting"] = False
            containers[container_id]["up"] = False
            containers[container_id]["logging"] = False
            containers[container_id]["players"] = []
            save_containers()
            asyncio.create_task(start_loop(bot, container_id))  # start loop first
            await startserver(bot, container_id)
            await msg.edit(content=f"{containers[container_id]["server"]} server crashed, but is now back online.")
            log(f"{containers[container_id]['server']} server in container {containers[container_id]['nick']} is back online after crash")
            containers[container_id]["lastrevive"] = time.time()
            save_containers()

async def handle_message(bot, message):
    container_id = get_containerid_from_channelid(message.channel.id)

    if message.author == bot.user:
        return

    if container_id is None:
        return

    if message.channel.id == containers[container_id]["chat_id"]:
        command(f'tellraw @a [{{"text":"<","color":"blue","bold":true}},{{"text":"{message.author.global_name}"}},{{"text":"> ","color":"blue","bold":true}},{{"text":"{message.content}","color":"white", "bold":false}}]', container_id)
        #command(f"say §9<{message.author.global_name}>§r {message.content}", container_id)
    elif message.channel.id == containers[container_id]["console_id"]:
        try:
            if check_console_perm_msg(message):
                response = command(message.content, container_id)
                if response and response.strip():
                    await message.channel.send(f"```{response}```")
        except CheckFailure as error:
            await message.channel.send(str(error))
