import os, asyncio, socket, time
from pathlib import Path
from dotenv import load_dotenv
from utils.utilities import animate, dm_superuser
from utils.perms import check_console_perm_msg
from utils.data import containers, save_containers, get_containerid_from_channelid
from utils.networking import command, is_server_up

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

def build_run(text):
    return f'start "" "{SERVER_DIR}/{text}/{RUNFILE}"'

def build_log(text):
    return f"{SERVER_DIR / text / 'logs' / 'latest.log'}"

def build_whitelist(text):
    return f"{SERVER_DIR / text / 'whitelist.json'}"

def build_properties(text):
    return f"{SERVER_DIR / text / 'server.properties'}"
        
async def server_start_loop(self, msg):
    container_id = get_containerid_from_channelid(msg.channel.id)
    containers[container_id]["starting"] = True
    starttime = time.time()
    asyncio.create_task(animate(msg))
    while containers[container_id]["starting"]:
        if time.time() - starttime > 300:
            await msg.edit(content=f"❌ Server failed to start within 5 minutes.")
            containers[container_id]["starting"] = False
            save_containers()
            return
        if is_server_up(container_id):
            print("server is up")
            containers[container_id]["up"] = True
            save_containers()
            if not containers[container_id]["logging"]:
                print("log is off, starting log")
                from utils.polling import startlogging
                await startlogging(self, container_id)
            print("serverstarting setting to 0...")
            containers[container_id]["starting"] = False
            save_containers()
            print("serverstarting successfully set to 0")
            await msg.edit(content=f"✅ {containers[container_id]["server"]} Server is now online! ✅")
            return
        await asyncio.sleep(POLLSECONDS)

async def startserver(self, msg):
    container_id = get_containerid_from_channelid(msg.channel.id)
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
    print(f"checking for path {runfilepath}")
    if not os.path.exists(runfilepath):
        print("generating run.bat")
        #generate_run_bat(server_name)

    print("starting " + containers[container_id]["server"] + " server")
    await asyncio.create_subprocess_shell(
        build_run(containers[container_id]["server"]),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await server_start_loop(self, msg)

async def stopserver(msg):
    container_id = get_containerid_from_channelid(msg.channel.id)
    command("stop", container_id)
    containers[container_id]["up"] = False
    containers[container_id]["logging"] = False
    save_containers()
    await msg.edit(content=f"❌ {containers[container_id]["server"]} Server is now offline! ❌")

async def checkserversup(self):
    print("Checking if any servers are down...")
    
    for container_id, container_data in containers.items():
        print(f"Checking container {container_data["nick"]} for crashes...")
        
        if not is_server_up(container_id):
            
            if containers[container_id]["up"]:
                server_name = containers[container_id]["server"]
                print(f"Server crashed for container: {container_id}, on server {server_name}, restarting...")
                
                try:   
                    command("stop", container_id)
                    print("successfully stopped server (shouldn't even get here, right?)")
                except: print("failed to stop server, already down")

                channel_id = container_data["bot_channel_id"]
                botchannel = self.bot.get_channel(channel_id)
                while not botchannel:
                    await asyncio.sleep(3)
                    botchannel = self.bot.get_channel(channel_id)
                
                previousrevive = containers[container_id]["lastrevive"]
                if time.time() - previousrevive < 600:
                    print("Two crashes within 10 minutes, catestrophic error:")
                    perm_id = containers[container_id]["bot_perm"]
                    await botchannel.send(f"{server_name} server has crashed twice in 10 minutes. Please check in <@&{perm_id}>")
                    containers[container_id]["up"] = False
                    save_containers()
                    return

                await botchannel.send(f"{server_name} server appears to be down. Attempting to restart...")
                msg = await botchannel.send(f"{server_name} server is restarting...")
                containers[container_id]["starting"] = False
                containers[container_id]["up"] = False
                containers[container_id]["logging"] = False
                await startserver(self, msg)
                print("successfully started server, hopefully...")
                containers[container_id]["lastrevive"] = time.time()
                save_containers()

async def handle_message(self, message):
    if message.author == self.bot.user:
        return

    container_id = get_containerid_from_channelid(message.channel.id)
    from utils.minecraft import command
    if message.channel.id == containers[container_id]["chat_id"]:
        command(f"say §9<{message.author.global_name}>§r {message.content}", container_id)
    elif message.channel.id == containers[container_id]["console_id"]:
        if check_console_perm_msg(message):
            response = command(message.content, container_id)
            if response.strip():
                await message.channel.send(f"```{response}```")

def get_server_loader(server_name: str) -> str:
    server_path = SERVER_DIR / server_name

    if not server_path.is_dir():
        raise ValueError(f"Server '{server_name}' does not exist")

    # --- Forge / NeoForge ---
    libs = server_path / "libraries"
    if libs.exists():
        if (libs / "net" / "neoforged").exists():
            return "neoforge"
        if (libs / "net" / "minecraftforge").exists():
            return "forge"

    # --- Fabric / Quilt ---
    for jar in server_path.glob("*.jar"):
        name = jar.name.lower()
        if "quilt" in name:
            return "quilt"
        if "fabric" in name:
            return "fabric"

    # --- Paper / Spigot ---
    for jar in server_path.glob("*.jar"):
        name = jar.name.lower()
        if name.startswith("paper"):
            return "paper"
        if name.startswith("spigot"):
            return "spigot"

    # --- Vanilla ---
    for jar in server_path.glob("*.jar"):
        name = jar.name.lower()
        if name == "server.jar" or name.startswith("minecraft_server"):
            return "vanilla"

    return "unknown"

def read_server_properties(server: str) -> dict[str, str]:
    props = {}
    with open(build_properties(server), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                props[k] = v
    return props

def write_server_properties(server: str, props: dict[str, str]):
    output = []
    seen = set()

    with open(build_properties(server), "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                output.append(line)
                continue

            k, _ = stripped.split("=", 1)
            if k in props:
                output.append(f"{k}={props[k]}\n")
                seen.add(k)
            else:
                output.append(line)

    for k, v in props.items():
        if k not in seen:
            output.append(f"{k}={v}\n")

    with open(build_properties(server), "w", encoding="utf-8") as f:
        f.writelines(output)

def find_server_jar(server_dir: str, loader: str) -> str | None:
    files = os.listdir(server_dir)

    if loader == "vanilla":
        for f in files:
            if f == "server.jar":
                return f

    if loader == "spigot":
        for f in files:
            if f.startswith("spigot-") and f.endswith(".jar"):
                return f

    if loader == "paper":
        for f in files:
            if f.startswith("paper-") and f.endswith(".jar"):
                return f

    if loader == "fabric":
        for f in files:
            if f.endswith(".jar") and "fabric" in f.lower():
                return f

    if loader == "forge":
        for f in files:
            if f.endswith(".jar") and "forge" in f.lower():
                return f

    if loader == "neoforge":
        for f in files:
            if f.endswith(".jar") and "neoforge" in f.lower():
                return f

    return None

def generate_run_bat(server_name: str):
    loader = get_server_loader(server_name)
    server_dir = SERVER_DIR / server_name
    jar = find_server_jar(server_dir, loader)
    if not jar:
        raise FileNotFoundError(f"No server jar found for loader '{loader}'")

    content = RUN_BAT_TEMPLATE.format(jar=jar)

    path = os.path.join(server_dir, "run.bat")
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)