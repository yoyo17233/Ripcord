import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Example usage
install("discord")
install("mcrcon")
install("python-dotenv")