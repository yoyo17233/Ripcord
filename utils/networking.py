import os, socket
from dotenv import load_dotenv
from mcrcon import MCRcon
from utils.data import containers

load_dotenv()

local_ip = socket.gethostbyname(socket.gethostname())
RCON_IP = local_ip
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

def is_server_up(container_id):
    port = containers[container_id]["port"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.1)
        result = sock.connect_ex(('127.0.0.1', port))
        return result == 0

def command(command_name, container_id):
    try:
        rconport = containers[container_id]["port"] + 10000
        with MCRcon(RCON_IP, RCON_PASSWORD, port=rconport) as mcr:
            response = mcr.command(command_name)
        return response
    except Exception as e:
        print("error happened sending message")
        return e