import json, os, discord
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
SERVER_PATH = os.getenv("SERVER_DIR")
SERVER_DIR = Path(SERVER_PATH)

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

print(get_server_loader("ATM10"))