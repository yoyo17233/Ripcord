import json, os, asyncio, socket
from datetime import datetime, timedelta
from google import genai
from dotenv import load_dotenv

load_dotenv()
CONFIG_FILE = os.getenv("CONFIG_FILE")
GEMINIKEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINIKEY)
YEET = os.getenv("YEET")

SERVER_DIR = os.getenv("SERVER_DIR")
LOG_LOCATION = os.getenv("LOG_LOCATION")
RUNFILE = os.getenv("RUNFILE")
WHITELIST = "whitelist.json"

SLEEPTIME = 0.5

hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
RCON_IP = local_ip
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_server_info(guild_id=None):
    if guild_id is None:
        guild_id = YEET
    config = load_config()
    return config["guilds"][str(guild_id)].get("ServerInfo", {})

def update_server_info(key, value, guild_id=None):
    if guild_id is None:
        guild_id = YEET
    config = load_config()
    guild = config["guilds"][str(guild_id)]
    if "ServerInfo" not in guild:
        guild["ServerInfo"] = {}
    guild["ServerInfo"][key] = value
    save_config(config)

def get_facts() -> str:
    with open("facts.txt", "r", encoding="utf-8") as f:
        return f.read()

def set_random_fact(new_fact: str):
    facts_file = "facts.txt"
    try:
        with open(facts_file, "r", encoding="utf-8") as f:
            facts = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        facts = []

    facts.insert(0, new_fact)
    facts = facts[:60]

    with open(facts_file, "w", encoding="utf-8") as f:
        f.write("\n".join(facts) + "\n")

async def wait_until_10am():
    now = datetime.now()
    target = now.replace(hour=10, minute=0, second=0, microsecond=0)
    #target = now + timedelta(seconds=10)  # For testing, set to 10 seconds later
    if now >= target:
        target += timedelta(days=1)
    await asyncio.sleep((target - now).total_seconds())
    
def ask_gemini(prompt: str) -> str:
    print(f"Sending prompt to Gemini")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    print("Received response from Gemini: ", response.text)
    return response.text

async def animate(msg, guild_id):
    serverid = get_server_info(guild_id).get("serverid")
    dots = -1
    while get_server_info(guild_id).get("serverstarting"):
        dots = (dots + 1) % 3
        await msg.edit(content=f"Starting {serverid} server{'.' * (dots + 1)}")
        await asyncio.sleep(SLEEPTIME)
