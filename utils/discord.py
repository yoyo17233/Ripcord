import discord, asyncio
from utils.minecraft import startserver, stopserver
from utils.data import containers, save_containers
from utils.networking import is_server_up


# =========================
# VIEW
# =========================
class ServerControlView(discord.ui.View):
    def __init__(self, container_id):
        super().__init__(timeout=None)

        self.container_id = container_id
        server = containers[container_id]

        running = server["up"]
        starting = server["starting"]

        self.start_button.disabled = running or starting
        self.stop_button.disabled = (not running) or starting


    # =========================
    # START BUTTON
    # =========================
    @discord.ui.button(label="Start", style=discord.ButtonStyle.success)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        container_id = self.container_id

        if is_server_up(container_id):
            return await interaction.response.send_message(
                "Server is already running!",
                ephemeral=True
            )

        if containers[container_id]["starting"]:
            return await interaction.response.send_message(
                "Server is already starting...",
                ephemeral=True
            )

        if not containers[container_id]["server"]:
            return await interaction.response.send_message(
                "No server selected. Use /server first.",
                ephemeral=True
            )

        await interaction.response.defer()

        containers[container_id]["starting"] = True
        save_containers()
        print("starting server...")
        asyncio.create_task(start_loop(interaction.client, container_id))  # start loop first
        await startserver(interaction.client, container_id)


    # =========================
    # STOP BUTTON
    # =========================
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        container_id = self.container_id

        if not is_server_up(container_id):
            return await interaction.response.send_message(
                "Server isn't running.",
                ephemeral=True
            )

        await interaction.response.defer()

        await stopserver(container_id)
        await refresh_panel(interaction.client, container_id)


    # =========================
    # REFRESH BUTTON
    # =========================
    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await refresh_panel(interaction.client, self.container_id)


# =========================
# EMBED BUILDER
# =========================
def generate_embed(container):
    if container["starting"]:
        status = "Starting..."
        color = discord.Color.yellow()
    elif container["up"]:
        status = "On ✅"
        color = discord.Color.green()
    else:
        status = "Off ❌"
        color = discord.Color.red()

    playerlist = container.get("players", [])
    if not isinstance(playerlist, list):
        playerlist = []

    num = len(playerlist)
    player_value = "\n".join(playerlist) if playerlist else "No players online."

    embed = discord.Embed(
        title=f"{container['server']} Server",
        color=color
    )

    embed.add_field(name="Server Status", value=status, inline=True)

    embed.add_field(name=f"Playerlist ({num})", value=player_value, inline=True)

    embed.add_field(
        name="Channels",
        value=f"Chat: <#{container['chat_id']}>\nConsole: <#{container['console_id']}>",
        inline=False
    )

    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text="Minecraft Server Manager")

    return embed


# =========================
# PANEL MANAGEMENT
# =========================
async def send_control_panels(bot):
    for container_id in containers.keys():
        await refresh_panel(bot, container_id)


async def refresh_panel(bot, container_id):
    container = containers[container_id]
    channel = await bot.fetch_channel(container["bot_channel_id"])
    if not channel:
        return
    embed = generate_embed(container)
    view = ServerControlView(container_id)
    
    old_msg = None
    panel_message_id = container.get("panel_message")
    if panel_message_id:
        try:
            old_msg = await channel.fetch_message(int(panel_message_id))
        except discord.NotFound:
            print("Old panel message was deleted, sending a new one.")

    new_msg = await channel.send(embed=embed, view=view)
    if old_msg:
        await old_msg.delete()
    container["panel_message"] = new_msg.id
    save_containers()

async def start_loop(client, container_id):
    await refresh_panel(client, container_id)
    await asyncio.sleep(1)
    await refresh_panel(client, container_id)
    while containers[container_id]["starting"]:
        await asyncio.sleep(1)
    await refresh_panel(client, container_id)
