import os
import time
from dotenv import load_dotenv

load_dotenv()

SUPERUSERS = os.getenv("SUPERUSERS")
superusers = [int(x) for x in SUPERUSERS.split(",") if x.strip()]

DMS = os.getenv("DMS", "False").lower() in ("true", "1", "yes")
userToDm_id = superusers[0]

SLEEPTIME = 0.5

async def dm_user(bot, user_id, message):
    if(not DMS):
       #log(f"User DMs disabled, skipping...")
       return
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        log(f"DM sent to {user.global_name}")
    except Exception as e:
        log(f"Failed to DM user: {e}")

async def dm_superuser(bot, message):
    if(not DMS):
       #log(f"User DMs disabled, skipping...")
       return
    try:
        user = await bot.fetch_user(superusers[0])
        await user.send(message)
        log(f"DM sent to {user.global_name}")
    except Exception as e:
        log(f"Failed to DM user: {e}")

def log(message, type="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{timestamp}] [{type}]: {message}")
