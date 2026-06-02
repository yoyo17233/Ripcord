import copy
import json, os, discord, uuid
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
CONTAINER_FILE = "containers.json"
SERVER_PATH = os.getenv("SERVER_DIR")
SERVER_DIR = Path(SERVER_PATH)

DEFAULT_CONTAINER = {
    "bot_perm": 0,
    "console_perm": 0,

    "guild_id":0,
    "nick":"",

    "bot_channel_id": 0,
    "chat_id": 0,
    "console_id": 0,

    "port":0,
    "server":"",
    "allowed_servers":[],

    "logging":False,
    "up":False,
    "starting":False,
    "autorestarting":False,
    "lastrevive":0,
    "panel_message": 0,
    "players": []
}

def load_containers():
    if not os.path.exists(CONTAINER_FILE):
        with open(CONTAINER_FILE, "w") as f:
            json.dump({}, f, indent=4)
    with open(CONTAINER_FILE, "r") as f:
        loaded = json.load(f)

    updated = False
    for container_data in loaded.values():
        for key, value in DEFAULT_CONTAINER.items():
            if key not in container_data:
                container_data[key] = copy.deepcopy(value)
                updated = True

    if updated:
        with open(CONTAINER_FILE, "w") as f:
            json.dump(loaded, f, indent=4)

    return loaded

def save_containers():
    with open(CONTAINER_FILE, "w") as f:
        json.dump(containers, f, indent=4)

def init_guilds(bot):
    to_delete = []

    bot_guild_ids = [guild.id for guild in bot.guilds]
    for container_key, container_data in containers.items():
        guild_id_str = container_data.get("guild_id")
  
        guild_id = int(guild_id_str)

        if guild_id not in bot_guild_ids:
            to_delete.append(container_key)
            print(f"Deleted container {container_key} for missing guild {guild_id}")

    for k in to_delete:
        del containers[k]

    save_containers()

def get_servers():
    return [
        name
        for name in os.listdir(SERVER_DIR)
        if os.path.isdir(os.path.join(SERVER_DIR, name))
    ]

def create_container(interaction: discord.Interaction, nick, bot_perms, console_perms, chat_id, console_id, port):
    guild_id = interaction.guild_id
    bot_channel_id = interaction.channel_id

    if port >= 30000 or port < 20000:
        return 1
    
    for container in containers.values():
        if (container["guild_id"] == guild_id and container["nick"] == nick):
            return 2
    
    new_ids = [bot_channel_id, console_id, chat_id]
    for container in containers.values():
        for existing_id in [container["bot_channel_id"], container["chat_id"], container["console_id"]]:
            if existing_id != 0 and existing_id in new_ids:
                return 3
            
    id = uuid.uuid4().hex
    containers[id] = copy.deepcopy(DEFAULT_CONTAINER)
    containers[id]["nick"] = nick
    containers[id]["guild_id"] = guild_id
    containers[id]["bot_perm"] = bot_perms
    containers[id]["console_perm"] = console_perms
    containers[id]["bot_channel_id"] = bot_channel_id
    containers[id]["chat_id"] = chat_id
    containers[id]["console_id"] = console_id
    containers[id]["port"] = port
    save_containers()
    return id

def link_server(interaction: discord.Interaction, server_name):
    if not (server_name in servers):
        return
    container_id = get_containerid_from_interaction(interaction)
    if server_name in containers[container_id]["allowed_servers"]:
        return
    containers[container_id]["allowed_servers"].append(server_name)
    save_containers()

def swap_server(interaction: discord.Interaction, server_name):
    container_id = get_containerid_from_interaction(interaction)
    if not (server_name in containers[container_id]["allowed_servers"]):
        return
    if containers[container_id]["server"] == server_name:
        return
    containers[container_id]["server"] = server_name
    save_containers()

def get_containerid_from_interaction(interaction: discord.Interaction):
    for container_id, container_data in containers.items():
        if interaction.channel_id in (
            container_data.get("bot_channel_id"),
            container_data.get("chat_id"),
            container_data.get("console_id")
        ):
            return container_id
    return None 

def get_containerid_from_channelid(channel_id):
    for container_id, container_data in containers.items():
        if channel_id in (
            container_data.get("bot_channel_id"),
            container_data.get("chat_id"),
            container_data.get("console_id")
        ):
            return container_id
    return None 

def get_containerids_from_guildid(guild_id):
    guild_id_str = str(guild_id)
    container_ids = []

    for container_id, container_data in containers.items():
        container_guild_id = container_data.get("guild_id")
        if container_guild_id == guild_id_str:
            container_ids.append(container_id)

    return container_ids

containers = load_containers()
servers = get_servers()
