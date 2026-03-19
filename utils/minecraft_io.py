import os, socket
from pathlib import Path
from dotenv import load_dotenv

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

