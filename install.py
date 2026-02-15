import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install("discord")
install("mcrcon")
install("python-dotenv")