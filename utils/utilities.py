import os
from utils.perms import superusers

DMS = os.getenv("DMS", "False").lower() in ("true", "1", "yes")
userToDm_id = superusers[0]

SLEEPTIME = 0.5

async def dm_user(bot, user_id, message):
    if(not DMS):
       #print(f"User DMs disabled, skipping...")
       return
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        print(f"DM sent to {user.global_name}")
    except Exception as e:
        print(f"Failed to DM user: {e}")

async def dm_superuser(bot, message):
    if(not DMS):
       #print(f"User DMs disabled, skipping...")
       return
    try:
        user = await bot.fetch_user(superusers[0])
        await user.send(message)
        print(f"DM sent to {user.global_name}")
    except Exception as e:
        print(f"Failed to DM user: {e}")