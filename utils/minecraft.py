import os, asyncio, socket, time
from dotenv import load_dotenv
from utils.utilities import animate
from utils.perms import check_console_perm_msg
from utils.data import containers, save_containers, get_containerid_from_channelid
from utils.networking import command, is_server_up

load_dotenv()

SERVER_DIR = os.getenv("SERVER_DIR")
LOG_LOCATION = os.getenv("LOG_LOCATION")
RUNFILE = os.getenv("RUNFILE")

POLLSECONDS = 3

VERBOSE = False

local_ip = socket.gethostbyname(socket.gethostname())
RCON_IP = local_ip
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

def build_run(text):
    return f'start "" "{SERVER_DIR}{text}/{RUNFILE}"'

def build_log(text):
    return f"{SERVER_DIR}{text}/{LOG_LOCATION}"

def build_whitelist(text):
    return f"{SERVER_DIR}{text}/whitelist.json"
        
async def server_start_loop(self, msg):
    container_id = get_containerid_from_channelid(msg.channel.id)
    containers[container_id]["starting"] = True
    starttime = time.time()
    asyncio.create_task(animate(msg, container_id))
    while containers[container_id]["starting"]:
        if time.time() - starttime > 180:
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
    save_containers()
    await msg.edit(content=f"❌ {containers[container_id]["server"]} Server is now offline! ❌")

async def checkserversup(self):
    print("Checking if any servers are down...")
    
    for container_id, container_data in containers.items():
        print(f"Checking container {container_id} for crashes...")
        
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