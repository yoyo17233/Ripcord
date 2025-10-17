import os, sys, io
from dotenv import load_dotenv
import discord
from discord.ext import commands
from utils.utilities import update_server_info, get_server_info, load_config, save_config
from utils.minecraft import is_server_up
from cogs.yeetbot import startlogging

VERBOSE = True

DEFAULT_GUILD_CONFIG = {
    "snoopie_channel_id": 1,
    "snoopie_role_id": 1,
    "snoopie_perms_role_id": 1,
    "mc_perms_role_id": 1,
    "mc_console_perms_role_id": 1,
    "mc_bot_channel_id": 1,
    "mc_chat_channel_id": 1,
    "mc_console_channel_id": 1,
    "ServerInfo": {
        "logging": 0,
        "up": 0,
        "serverstarting": 0,
        "serverid": "servername",
        "serverport": 25567,
        "deathmsg": "chat",
        "lastrevival": 0
    },
    "ServerList": [
        "servername1",
        "servername2"
    ]
}

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
YEET = os.getenv("YEET")

CONFIG_FILE = os.getenv("CONFIG_FILE")
config = load_config()

intents = discord.Intents.default()
intents.message_content = True  
intents.guilds = True  

initialized = False     

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():

    yoyo_id = 242420160227573760  # Replace with target user's ID
    yoyo = await bot.fetch_user(yoyo_id)
    try:
        await yoyo.send("on_ready called")
        print("DM sent.")
    except discord.Forbidden:
        print("Could not send DM — user has DMs disabled or blocked the bot.")

    global initialized
    if(initialized): return
    else: initialized = True
        
    try:
        await yoyo.send("on_ready passed init check")
        print("DM sent.")
    except discord.Forbidden:
        print("Could not send DM — user has DMs disabled or blocked the bot.")

    global config
    config["console_emptier"] = 0
    save_config(config)
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
        
        await bot.change_presence(
            activity=discord.Game(f"Minecraft ✅"),
            status=discord.Status.online
        )
        for guild in bot.guilds:
            update_server_info("serverstarting", 0, guild.id)
            if is_server_up(guild.id):
                update_server_info("up", 1, guild.id)
                print(f"Starting logging for guild {guild.id}")
                await startlogging(bot.get_cog("YeetBot"), guild.id)
            else:
                update_server_info("up", 0, guild.id)
                update_server_info("logging", 0, guild.id)

    except Exception as e:
        print(f"Error syncing commands: {e}")
    updated = False

    for guild in bot.guilds:
        print("checking guild", guild.id)
        if str(guild.id) not in config["guilds"]:
            config["guilds"][str(guild.id)] = DEFAULT_GUILD_CONFIG
            updated = True

    if updated:
        save_config(config)

async def load_cogs():
    await bot.load_extension("cogs.snoopiebot")
    await bot.load_extension("cogs.yeetbot")
    await bot.load_extension("cogs.idsetter")

@bot.event
async def setup_hook():
    await load_cogs()

bot.run(TOKEN)