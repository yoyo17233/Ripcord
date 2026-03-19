import discord, asyncio
from utils.minecraft import startserver, stopserver
from utils.data import containers
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
        server = containers[container_id]

        if is_server_up(container_id):
            return await interaction.response.send_message(
                "Server is already running!",
                ephemeral=True
            )

        if server["starting"]:
            return await interaction.response.send_message(
                "Server is already starting...",
                ephemeral=True
            )

        if not server["server"]:
            return await interaction.response.send_message(
                "No server selected. Use /server first.",
                ephemeral=True
            )

        await interaction.response.defer()

        await interaction.followup.send(
            f"🚀 Starting **{server['server']}**...",
            wait=True
        )

        await startserver(interaction.client, container_id)
        asyncio.create_task(double_refresh(interaction.client, container_id))


    # =========================
    # STOP BUTTON
    # =========================
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        container_id = self.container_id
        server = containers[container_id]

        if not is_server_up(container_id):
            return await interaction.response.send_message(
                "Server isn't running.",
                ephemeral=True
            )

        await interaction.response.defer()

        await interaction.followup.send(
            "🛑 Stopping server...",
            wait=True
        )

        await stopserver(interaction.client, container_id)
        asyncio.create_task(double_refresh(interaction.client, container_id))


    # =========================
    # REFRESH BUTTON
    # =========================
    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        container_id = self.container_id
        server = containers[container_id]

        embed = generate_embed(server)
        view = ServerControlView(container_id)

        await interaction.response.edit_message(embed=embed, view=view)


# =========================
# EMBED BUILDER
# =========================
def generate_embed(server):
    if server["starting"]:
        status = "Starting..."
        color = discord.Color.yellow()
    elif server["up"]:
        status = "On"
        color = discord.Color.green()
    else:
        status = "Off"
        color = discord.Color.red()

    embed = discord.Embed(
        title=f"{server['server']} Server",
        color=color
    )

    embed.add_field(name="Server Status", value=status, inline=True)

    embed.add_field(
        name="Channels",
        value=f"Chat: <#{server['chat_id']}>\nConsole: <#{server['console_id']}>",
        inline=False
    )

    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text="Minecraft Server Manager")

    return embed


# =========================
# PANEL MANAGEMENT
# =========================
async def send_control_panels(bot):
    for container_id, server in containers.items():
        channel = bot.get_channel(server["bot_channel_id"])
        if not channel:
            continue

        embed = generate_embed(server)
        view = ServerControlView(container_id)

        msg = await channel.send(embed=embed, view=view)
        server["panel_message"] = msg.id


async def refresh_panel(bot, container_id):
    server = containers[container_id]

    channel = bot.get_channel(server["bot_channel_id"])
    if not channel:
        return

    try:
        message = await channel.fetch_message(server["panel_message"])
    except Exception:
        return  # message deleted or missing

    embed = generate_embed(server)
    view = ServerControlView(container_id)

    await message.edit(embed=embed, view=view)


async def double_refresh(bot, container_id, delay=1):
    for _ in range(3):
        await refresh_panel(bot, container_id)
        await asyncio.sleep(delay)