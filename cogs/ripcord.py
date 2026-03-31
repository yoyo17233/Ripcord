import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.app_commands import AppCommandError, CheckFailure
from utils.perms import has_bot_perm, is_admin, check_is_server_up, is_bot_channel
from utils.minecraft import checkserversup, handle_message
from utils.minecraft_io import get_server_loader
from utils.polling import get_active_log_names
from utils.data import containers, get_containerid_from_channelid, save_containers, servers, create_container, get_containerid_from_interaction
from utils.networking import is_server_up, command
from utils.discord import refresh_panel
from typing import Union

async def server_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    container_id = get_containerid_from_interaction(interaction)
    allowed = containers[container_id]["allowed_servers"]
    choices = ["Check", *allowed]
    return [
        app_commands.Choice(name=server, value=server)
        for server in choices
        if current.lower() in server.lower()
    ]

async def allowserver_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=server, value=server)
        for server in servers
        if current.lower() in server.lower() and server.lower() != "archive"
    ]

async def container_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    choices = []

    for container_id, container_data in containers.items():
        nick = container_data.get("nick", "")
        container_guild_id = int(container_data.get("guild_id"))
        if container_guild_id != interaction.guild_id:
            continue
        if current.lower() in nick.lower():
            choices.append(app_commands.Choice(name=nick, value=container_id))

    return choices

class Ripcord(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.checkservervalue.start()
        
    @tasks.loop(minutes=1)
    async def checkservervalue(self):
        await checkserversup(self.bot)

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.DMChannel):
            print("message channel is DM, skipping")
            return
        if message.author == self.bot.user:
            return
        if message.channel.id in [container_data.get("bot_channel_id") for container_data in containers.values()]:
            await refresh_panel(self.bot, get_containerid_from_channelid(message.channel.id))
            return
        await handle_message(self.bot, message)

    @app_commands.command(name="createcontainer", description="Creates a new container object to hold a server")
    @is_admin()
    async def createContainer(
        self, 
        interaction: discord.Interaction, 
        botperm: discord.Role, 
        consoleperm: discord.Role,
        nickname: str, 
        chatchannel: Union[discord.TextChannel, discord.Thread],
        consolechannel: Union[discord.TextChannel, discord.Thread], 
        port: int):
        await interaction.response.defer(ephemeral=True)
        result = create_container(interaction, nickname, botperm.id, consoleperm.id, chatchannel.id, consolechannel.id, port)
        if not isinstance(result, str):
            await interaction.followup.send(f"Creation of container {nickname} failed with error code {result}", wait=True, ephemeral=True)
        else:
            await interaction.followup.send(f"Container {nickname} created with ID {result}", wait=True, ephemeral=True)

    @app_commands.command(name="server", description="Select a server to set as active")
    @app_commands.autocomplete(server=server_autocomplete)
    @app_commands.describe(server="Pick a server to set as active...")
    @is_bot_channel()
    @has_bot_perm()
    async def server(self, interaction: discord.Interaction, server: str):
        container_id = get_containerid_from_interaction(interaction)

        if server == "Check":
            await interaction.response.send_message(f"Current server is set to: {containers[container_id]['server']}", ephemeral=True)
            return

        if server not in containers[container_id]["allowed_servers"]:
            await interaction.response.send_message(
                f"Server `{server}` is not allowed for this container. "
                f"Add it with `/allowserver`.", ephemeral=True)
            return
        
        if is_server_up(container_id):
            await interaction.response.send_message(
            f"The container is already up with server {server}."
            f"You must first stop it with /stop to change the server.", ephemeral=True)
            return
        
        containers[container_id]["server"] = server
        save_containers()
        await interaction.response.send_message(f"Server `{server}` has been set for this container. ", ephemeral=True)

    @app_commands.command(name="allowserver", description="Allows a server to a container")
    @app_commands.autocomplete(server=allowserver_autocomplete)
    @is_bot_channel()
    @is_admin()
    async def allowserver(self, interaction: discord.Interaction, server: str):
        container_id = get_containerid_from_interaction(interaction)

        if not server in servers:
            await interaction.response.send_message(f"{server} Directory not found", ephemeral=True)
            return

        if server in containers[container_id]["allowed_servers"]:
            await interaction.response.send_message(f"{server} is already allowed", ephemeral=True)
            return
        
        containers[container_id]["allowed_servers"].append(server)
        save_containers()
        await interaction.response.send_message(f"{server} has been added to container {containers[container_id]["nick"]}", ephemeral=True)

    @app_commands.command(name="container", description="gives information about the current containers")
    @app_commands.autocomplete(container=container_autocomplete)
    @app_commands.describe(container="Select a container to get information for")
    @is_bot_channel()
    @has_bot_perm()
    async def container(self, interaction: discord.Interaction, container: str):
        container_id = container
        guild = await self.bot.fetch_guild(containers[container_id]['guild_id'])
        containers[container_id]["bot_perm"]
        message_text = (
            f"{container}:\n"
            f"General Perm = <@&{containers[container_id]['bot_perm']}>\n"
            f"Console Perm = <@&{containers[container_id]['console_perm']}>\n"
            f"Guild = {guild.name}\n"
            f"Nick = {containers[container_id]['nick']}\n"
            f"Bot Channel = <#{containers[container_id]['bot_channel_id']}>\n"
            f"Chat Channel = <#{containers[container_id]['chat_id']}>\n"
            f"Console Channel = <#{containers[container_id]['console_id']}>\n"
            f"Port = {containers[container_id]['port']}\n"
            f"Active Server = {containers[container_id]['server']}\n"
            f"Allowed Servers = {containers[container_id]['allowed_servers']}\n"
            f"Logging = {containers[container_id]['logging']}\n"
            f"Up = {containers[container_id]['up']}\n"
            f"Starting = {containers[container_id]['starting']}\n"
            f"Last Revive = {containers[container_id]['lastrevive']}"
        )        
        await interaction.response.send_message(
            message_text,
            ephemeral=True
        )

    @app_commands.command(name="ping", description="Responds \"Pong!\" - Used to test connection to the bot")
    @has_bot_perm()
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong!", ephemeral=True)

    @app_commands.command(name="status", description="Responds with the current status of the active server")
    @is_bot_channel()
    @has_bot_perm()
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        container_id = get_containerid_from_interaction(interaction)
        message = await interaction.followup.send("Pinging server...", wait=True)
        if is_server_up(container_id):
            containers[container_id]["starting"] = 0
            save_containers()
            await message.edit(content=f"✅ {containers[container_id]["server"]} Server is online! ✅")
        else:
            await message.edit(content=f"❌ {containers[container_id]["server"]} Server is offline! ❌")

    @app_commands.command(name="list", description="Lists the current players on the active server")
    @is_bot_channel()
    @has_bot_perm()
    @check_is_server_up()
    async def list(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"```{command('list', get_containerid_from_interaction(interaction))}```")

    @app_commands.command(name="tps", description="Sends information regarding Ticks Per Second of the server (SkyFactory only)")
    @is_bot_channel()
    @has_bot_perm()
    @check_is_server_up()
    async def tps(self, interaction: discord.Interaction):
        container_id = get_containerid_from_interaction(interaction)
        loader = get_server_loader(containers[container_id]["server"])
        tpsCommand = "tps"
        if loader == "neoforge":
            tpsCommand = "neoforge tps"
        if loader == "forge":
            tpsCommand = "forge tps"
        await interaction.response.send_message(f"```{command(tpsCommand, get_containerid_from_interaction(interaction))}```")

    @app_commands.command(name="help", description="Gives information about possible commands")
    @has_bot_perm()
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message("```\n"
                       "Commands:\n\n"
                       "/start                 - Start the server\n"
                       "/stop                  - Stop the server\n"
                       "/server                - Changes the active server\n"
                       "/allowserver           - Adds server to containers allowed server list\n"
                       "/ping                  - Ping the bot\n"
                       "/status                - Check server status\n"
                       "\n"
                       "/createcontainer       - Creates a container to hold a server\n"
                       "\t Bot Perm -> Permission to use the bot\n"
                       "\t Console Perm -> Permission to use the console\n"
                       "\t Nick -> Nickname for the container\n"
                       "\t Bot Channel -> Channel to give commands to the bot (Implicit from the channel where the command is run)\n"
                       "\t Chat Channel -> Channel for minecraft chat\n"
                       "\t Console Channel -> Channel for minecraft chat\n"
                       "\t Port -> Port for minecraft server to run on\n"
                       "/help                  - Show this message\n```\n", ephemeral=True)
        
    @app_commands.command(name="logging", description="Gives information about running logging threads")
    @has_bot_perm()
    async def logging(self, interaction: discord.Interaction):
        await interaction.response.send_message(get_active_log_names(), ephemeral=True)
                       
    async def cog_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, CheckFailure):
            if interaction.response.is_done():
                print(f"Check failed: {type(error).__name__}, message: {error}")
                await interaction.followup.send(f"Error: {error}", ephemeral=True)
            else:
                print(f"Check failed: {type(error).__name__}, message: {error}")
                await interaction.response.send_message(f"Error: {error}", ephemeral=True)
        else:
            print(f"Unhandled error: {error}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Ripcord(bot))