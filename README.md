# Ripcord
A Discord bot that bridges Discord and Minecraft — remotely manage servers, relay chat, and keep things running automatically.

This is a personal project built for my own Discord and Minecraft server. It supports running multiple Minecraft servers concurrently across multiple Discord servers, each isolated in its own "container." Values are persisted in `containers.json` across bot restarts.

Feel free to adapt it for your own server. If you find it useful, you're welcome to send a few bucks: https://buymeacoffee.com/yoyo4444

Questions or issues: timothy.kwartler@gmail.com or **yoyo.4444** on Discord

---

## Setup

1. Copy `.env.example` to `.env` and fill in all values.
2. Run `pip install -r requirements.txt`.
3. Start the bot with `startbot.bat` (or `python main-ripcord.py`).
4. Create at least one container with `/createcontainer` (see Admin Commands below).
5. Use `/allowserver` to add servers to the container, then `/server` to select one.

---

## Control Panel

When the bot starts, it posts a control panel embed in each container's bot channel with three buttons:

- **Start** — Start the active server
- **Stop** — Stop the running server
- **Refresh** — Refresh the embed with current status and player list

---

## Slash Commands

### Server Commands
| Command | Description |
|---------|-------------|
| `/server` | View or change the active server for this container |
| `/help` | Show the in-Discord help message |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/allowserver` | Allow a server directory to be used by this container |
| `/disallowserver` | Remove a server from the container's allowed list |
| `/container` | Show details and current state of a container |
| `/logging` | Show which containers currently have active log threads |
| `/createcontainer` | Create a new container (run from the desired bot channel) |

#### `/createcontainer` Parameters
| Parameter | Description |
|-----------|-------------|
| `botperm` | Role required to use general bot commands |
| `consoleperm` | Role required to send commands via the console channel |
| `nickname` | Display name for this container |
| `chatchannel` | Channel for Minecraft chat relay |
| `consolechannel` | Channel for server console output |
| `port` | Minecraft server port (must be in range 20000–29999) |

---

## Autorestart

Ripcord can restart the host machine on a daily schedule and automatically bring servers back online afterwards. Configure in `.env`:

```
AUTORESTART=true
AUTORESTART_HOUR=4        # 24-hour format — restart at 4:00 AM
ONLY_IF_EMPTY=true        # Only restart if no players are online
```

The bot saves which servers were running before the restart and starts them again on the next boot.
