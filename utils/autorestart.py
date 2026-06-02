import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from utils.data import containers, save_containers
from utils.minecraft import startserver, stopserver
from utils.networking import is_server_up
from utils.utilities import dm_superuser

load_dotenv()

RESTART_SCRIPT = "restartpc.bat"
POLL_SECONDS = 10
SHUTDOWN_GRACE_SECONDS = 180
ONLY_IF_EMPTY = os.getenv("ONLY_IF_EMPTY", "false").lower() in {"true", "1", "yes", "on"}

async def restart_precheck(bot):
    if ONLY_IF_EMPTY:
        for container in containers.values():
            if container.get("players"):
                await dm_superuser(bot, "Restart precheck failed: Container has players.")
                return False
    await dm_superuser(bot, "Restart precheck passed: No players online.")
    return True

def parse_autorestart_time():
    value = (os.getenv("AUTORESTART") or "").strip()
    hour_value = (os.getenv("AUTORESTART_HOUR") or "").strip()

    if value.lower() in {"", "false", "0", "no", "off"}:
        return None

    if value.lower() in {"true", "1", "yes", "on"}:
        if not hour_value:
            raise ValueError("AUTORESTART_HOUR is required when AUTORESTART=true")

    if ":" in hour_value:
        parts = hour_value.split(":")
        if len(parts) != 2:
            raise ValueError("AUTORESTART must be formatted as HH:MM")
        hour = int(parts[0])
        minute = int(parts[1])
    else:
        hour = int(hour_value)
        minute = 0

    validate_autorestart_time(hour, minute)
    return hour, minute


def validate_autorestart_time(hour, minute):
    if hour < 0 or hour > 23:
        raise ValueError("AUTORESTART hour must be from 0 to 23")
    if minute < 0 or minute > 59:
        raise ValueError("AUTORESTART minute must be from 0 to 59")


async def restore_autorestarting_servers(bot):
    for container_id, container in containers.items():
        if not container.get("autorestarting"):
            continue

        if is_server_up(container_id):
            container["autorestarting"] = False
            container["up"] = True
            save_containers()
            continue

        container["autorestarting"] = False
        container["starting"] = True
        container["up"] = False
        container["logging"] = False
        container["players"] = []
        save_containers()

        from utils.discord import start_loop

        asyncio.create_task(start_loop(bot, container_id))
        await startserver(bot, container_id)


async def stop_running_servers_for_restart():
    running_container_ids = [
        container_id
        for container_id, container in containers.items()
        if container.get("up") or is_server_up(container_id)
    ]

    for container_id, container in containers.items():
        container["autorestarting"] = container_id in running_container_ids
    save_containers()

    for container_id in running_container_ids:
        await stopserver(container_id)

    deadline = asyncio.get_running_loop().time() + SHUTDOWN_GRACE_SECONDS
    while asyncio.get_running_loop().time() < deadline:
        if all(not is_server_up(container_id) for container_id in running_container_ids):
            return
        await asyncio.sleep(POLL_SECONDS)

    raise TimeoutError("Timed out waiting for Minecraft servers to stop")


async def run_restart_script():
    restart_script = Path(RESTART_SCRIPT).resolve()
    await asyncio.create_subprocess_shell(f'"{restart_script}"')
