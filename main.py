import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from utils.utilities import dm_superuser
from utils.data import init_guilds

VERBOSE = True

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  
intents.guilds = True  

initialized = False     

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await dm_superuser(bot, "on_ready called")

    global initialized
    if(initialized): return
    else: initialized = True
        
    await dm_superuser(bot, "on_ready passed init check")

    init_guilds(bot)

    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
        
        await bot.change_presence(
            activity=discord.Game(f"Minecraft ✅"),
            status=discord.Status.online
        )

    except Exception as e:
        print(f"Error syncing commands: {e}")

async def load_cogs():
    await bot.load_extension("cogs.ripcord")

@bot.event
async def setup_hook():
    await dm_superuser(bot, "setup_hook called")
    await load_cogs()

bot.run(TOKEN)