import discord, asyncio
from utils.minecraft import startserver, stopserver
from utils.data import containers
from utils.networking import is_server_up
from utils.perms import has_bot_perm


class ServerControlView(discord.ui.View):
    def __init__(self, container_id):
        super().__init__(timeout=None)

        self.container_id = container_id
        serverInfo = containers[container_id]

        server_running = serverInfo["up"]
        server_starting = serverInfo["starting"]

        self.start_button.disabled = server_running or server_starting
        self.stop_button.disabled = (not server_running) or server_starting

    @discord.ui.button(label="Start", style=discord.ButtonStyle.success)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        container_id = self.container_id

        if is_server_up(container_id):
            await interaction.response.send_message("Server is already running!", ephemeral=True)
            return

        if containers[container_id]["starting"]:
            await interaction.response.send_message(
                "Server is already starting up, calm your tits!",
                ephemeral=True
            )
            return

        if not containers[container_id]["server"]:
            await interaction.response.send_message(
                "No server selected, select one using /server",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        await interaction.followup.send(
            f"Starting {containers[container_id]['server']} server",
            wait=True
        )

        await startserver(interaction.client, container_id)
        asyncio.create_task(double_refresh(interaction.client, container_id))


    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        container_id = self.container_id

        if not is_server_up(container_id):
            await interaction.response.send_message(
                "Server isn't running? Dumbass",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        msg = await interaction.followup.send(
            "Server shutting down...",
            wait=True
        )

        await stopserver(interaction.client, container_id)
        asyncio.create_task(double_refresh(interaction.client, container_id))


    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        container_id = self.container_id

        embed = generateEmbed(containers[container_id])
        view = ServerControlView(container_id)

        await interaction.response.edit_message(embed=embed, view=view)


def generateEmbed(serverInfo):

    status = "Off"
    if serverInfo["up"]:
        status = "On"
    if serverInfo["starting"]:
        status = "Starting..."

    chat = serverInfo["chat_id"]
    console = serverInfo["console_id"]

    usedColor = discord.Color.red()

    if status == "On":
        usedColor = discord.Color.green()
    elif status == "Starting...":
        usedColor = discord.Color.yellow()

    embed = discord.Embed(
        title=f"{serverInfo['server']} Server",
        color=usedColor
    )

    embed.add_field(
        name="Server Status",
        value=status,
        inline=True
    )

    embed.add_field(
        name="Channels",
        value=f"Chat: <#{chat}>\nConsole: <#{console}>",
        inline=False
    )

    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text="Minecraft Server Manager")

    return embed

async def send_control_panels(bot):
    for container_id, serverInfo in containers.items():

        channel_id = serverInfo["bot_channel_id"]
        channel = bot.get_channel(channel_id)

        if not channel:
            continue

        embed = generateEmbed(serverInfo)
        view = ServerControlView(container_id)

        msg = await channel.send(embed=embed, view=view)

        # store location for later refreshes
        containers[container_id]["panel_message"] = msg.id

async def refresh_panel(bot, container_id):
    
    serverInfo = containers[container_id]

    channel_id = serverInfo["bot_channel_id"]
    message_id = serverInfo["panel_message"]

    channel = bot.get_channel(channel_id)
    message = await channel.fetch_message(message_id)

    embed = generateEmbed(serverInfo)
    view = ServerControlView(container_id)

    await message.edit(embed=embed, view=view)

async def double_refresh(bot, container_id, delay=1):
    await refresh_panel(bot, container_id)
    await asyncio.sleep(delay)
    await refresh_panel(bot, container_id)
    await asyncio.sleep(delay)
    await refresh_panel(bot, container_id)