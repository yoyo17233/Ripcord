import os, asyncio
from utils.perms import superusers
from utils.data import containers, get_containerid_from_channelid
DMS = os.getenv("DMS", "False").lower() in ("true", "1", "yes")
userToDm_id = superusers[0]

SLEEPTIME = 0.5

def iterate_braille(braille: str) -> str:
    match braille:
        case "⠁": braille = "⠉"
        case "⠉": braille = "⠙"
        case "⠙": braille = "⠸"
        case "⠸": braille = "⠴"
        case "⠴": braille = "⠦"
        case "⠦": braille = "⠇"
        case "⠇": braille = "⠋"
        case "⠋": braille = "⠙"
    return braille

async def animate(msg):
    braille = "⠁"
    container_id = get_containerid_from_channelid(msg.channel.id)
    while containers[container_id]["starting"]:
        await msg.edit(content=f"Starting {containers[container_id]["server"]} server {str(braille)}")
        braille = iterate_braille(braille)
        await asyncio.sleep(SLEEPTIME)

async def dm_user(bot, user_id, message):
    if(not DMS):
       print(f"User DMs disabled, skipping...")
       return
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        print(f"DM sent to {user.global_name}")
    except Exception as e:
        print(f"Failed to DM user: {e}")

async def dm_superuser(bot, message):
    if(not DMS):
       print(f"User DMs disabled, skipping...")
       return
    try:
        user = await bot.fetch_user(superusers[0])
        await user.send(message)
        print(f"DM sent to {user.global_name}")
    except Exception as e:
        print(f"Failed to DM user: {e}")