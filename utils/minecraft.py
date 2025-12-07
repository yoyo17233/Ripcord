import os, asyncio, socket, time
from dotenv import load_dotenv
from mcrcon import MCRcon
from utils.utilities import update_server_info, animate, get_server_info, load_config

load_dotenv()
config = load_config()

SERVER_DIR = os.getenv("SERVER_DIR")
LOG_LOCATION = os.getenv("LOG_LOCATION")
RUNFILE = os.getenv("RUNFILE")
WHITELIST = "whitelist.json"

POLLSECONDS = 3

VERBOSE = False

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
RCON_IP = local_ip
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

def is_server_up(guild_id):
    port = get_server_info(guild_id).get("serverport")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.1)
        result = sock.connect_ex(('127.0.0.1', port))
        return result == 0

def build_run(text):
    return f'start "" "{SERVER_DIR}{text}/{RUNFILE}"'

def build_log(text):
    return f"{SERVER_DIR}{text}/{LOG_LOCATION}"

def build_whitelist(text):
    return f"{SERVER_DIR}{text}/{WHITELIST}"

def command(command_name, guild_id):
        try:
            if(VERBOSE):print(f"Executing command: {command_name}")
            if(VERBOSE):print("DEBUG guild_id:", guild_id)
            if(VERBOSE):print("DEBUG server_info:", get_server_info(guild_id))
            port = get_server_info(guild_id).get("serverport")
            if(VERBOSE):print("port retrieved as " + str(port))
            rconport = port + 10
            if(VERBOSE):print("RCON_IP: " + RCON_IP)
            if(VERBOSE):print("RCON_PASS: " + RCON_PASSWORD)
            if(VERBOSE):print("RCON_PORT: " + str(rconport))
            with MCRcon(RCON_IP, RCON_PASSWORD, port=rconport) as mcr:
                response = mcr.command(command_name)
            if response:
                if(VERBOSE):print(f"Command response: {response}")
            return response
        except Exception as e:
            print("error happened sending message")
            return e
        
async def server_status_check(self, msg, guild_id):
    update_server_info("serverstarting", 1, guild_id)
    starttime = time.time()
    asyncio.create_task(animate(msg, guild_id))
    while get_server_info(guild_id).get("serverstarting"):
        if time.time() - starttime > 180:
            await msg.edit(content=f"❌ Server failed to start within 5 minutes.")
            update_server_info("serverstarting", 0, guild_id)
            return
        if is_server_up(guild_id):
            print("server is up")
            update_server_info("up", 1, guild_id)
            if not get_server_info(guild_id).get("logging"):
                print("log is off, starting log")
                from utils.polling import startlogging
                await startlogging(self, guild_id)
            print("serverstarting setting to 0...")
            update_server_info("serverstarting", 0, guild_id)
            print("serverstarting successfully set to 0")
            await msg.edit(content=f"✅ {get_server_info(guild_id).get('serverid')} Server is now online! ✅")
            #await self.bot.change_presence(activity=discord.Game(f"{get_server_info(guild_id).get("serverid")}✅"))
            return
        await asyncio.sleep(POLLSECONDS)

async def startserver(self, msg, guild_id):
    print("starting " + get_server_info(guild_id).get("serverid") + " server")
    await asyncio.create_subprocess_shell(
        build_run(get_server_info(guild_id).get("serverid")),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await server_status_check(self, msg, guild_id)

async def stopserver(msg, guild_id):
    command("stop", guild_id)
    update_server_info("up", 0, guild_id)
    await msg.edit(content=f"❌ {get_server_info(guild_id).get('serverid')} Server is now offline! ❌")

async def checkserversup(self):
    print("Checking if any servers are down...")
    
    for guild_id, guild_data in config.get("guilds").items():
        print(f"Checking guild {guild_id} for crashes...")
        
        if not is_server_up(guild_id):
            server_info = get_server_info(guild_id)
            
            if server_info.get("up"):
                print(f"Server crashed for guild: {guild_id}, restarting...")
                
                try:   
                    command("stop", guild_id)
                    print("successfully stopped server (shouldn't even get here, right?)")
                except: print("failed to stop server, already down")

                channel_id = guild_data.get("mc_bot_channel_id")
                botchannel = self.bot.get_channel(channel_id)
                
                previousrevive = server_info.get("lastrevival")
                if time.time() - previousrevive < 600:
                    print("Two crashes within 10 minutes, catestrophic error:")
                    admin = guild_data.get("mc_console_perms_role_id")
                    if botchannel:
                        await botchannel.send(f"{server_info.get('serverid')} server has crashed twice in 10 minutes. Please check in <@&{admin}>")
                        update_server_info("up", 0, guild_id)
                        return

                if botchannel:
                    await botchannel.send(f"{server_info.get('serverid')} server appears to be down. Attempting to restart...")
                    msg = await botchannel.send(f"{server_info.get('serverid')} server is restarting...")
                    await startserver(self, msg, guild_id)
                    print("successfully started server, hopefully...")
                    update_server_info("lastrevival", time.time(), guild_id)
                else:
                    print(f"Could not find channel {channel_id} for guild {guild_id}.")
