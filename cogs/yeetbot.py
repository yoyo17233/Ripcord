import os, discord
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import app_commands
from discord.app_commands import AppCommandError, CheckFailure
from utils.polling import *
from utils.utilities import *
from utils.perms import *
from utils.minecraft import *

VERBOSE = True

load_dotenv()

config = load_config()

RCON_PASSWORD = os.getenv("RCON_PASSWORD")
LOGFILE = os.getenv("LOGFILE")
POLLSECONDS = 3

all_servers = [server for guild in config["guilds"].values() for server in guild["ServerList"]]

async def handle_message(self, message):
    if(VERBOSE): print("handling message...")
    if message.author == self.bot.user:
        return
    if(VERBOSE): print("message is not from a bot...")
    if(VERBOSE): print("message content = " + message.content)
    if(VERBOSE): print("message channel = " + str(message.channel.id))
    if message.channel.id == config.get("guilds").get(str(message.guild.id)).get("mc_chat_channel_id"):
        if(VERBOSE): print("channel matched, sending command")
        command(f"say §9<{message.author.global_name}>§r {message.content}", message.guild.id)
        if(VERBOSE): print("success chat send")
    elif message.channel.id == config.get("guilds").get(str(message.guild.id)).get("mc_console_channel_id"):
        if(VERBOSE): print("correct console channel")
        if has_mc_console_perm(message.guild, message.author):
            if(VERBOSE): print("yes perms")
            response = command(message.content, message.guild.id)
            if(VERBOSE): 
                if(response): print("response gotten, response looks like: " + response)
            if response.strip():
                if(VERBOSE): print("sending message...")
                await message.channel.send(f"```{response}```")

class YeetBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.checkservervalue.start()
        
    @tasks.loop(minutes=1)
    async def checkservervalue(self):
        await checkserversup(self)

    @commands.Cog.listener()
    @has_mc_perm()
    async def on_message(self, message):
        await handle_message(self, message)

    @app_commands.command(name="start", description="Starts the currently selected minecraft server")
    @has_mc_perm()
    async def start(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        if is_server_up(interaction.guild.id):
            await interaction.response.send_message("Server is already running!")
            return

        if get_server_info(interaction.guild.id).get("serverstarting"):
            await interaction.response.send_message("Server is already starting up, calm your tits!")
            return

        await interaction.response.defer()
        msg = await interaction.followup.send(f"Starting {get_server_info(interaction.guild.id).get('serverid')} server", wait=True)
        await startserver(self, msg, interaction.guild_id)

    @app_commands.command(name="stop", description="Stops the currently selected minecraft server")
    @has_mc_perm()
    async def stop(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        if not is_server_up(interaction.guild.id):
            await interaction.response.send_message("Server isn't running? Dumbass")
            return
        command("stop", interaction.guild_id)
        update_server_info("up", 0, interaction.guild_id)
        await interaction.response.send_message(f"❌ {get_server_info(interaction.guild.id).get('serverid')} Server is now offline! ❌")
        #await self.bot.change_presence(
        #    activity=discord.Game("Server Offline ❌"),
        #)

    @app_commands.command(name="restart", description="Restarts the currently selected minecraft server")
    @has_mc_perm()
    async def restart(self, interaction: discord.Interaction):
        msg = await interaction.original_response()
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return

        if not is_server_up(interaction.guild.id) and not get_server_info(interaction.guild.id).get("serverstarting"):
            await interaction.response.send_message("Server wasn't running... I suppose I'll start it though")
            await startserver(self.bot, interaction, interaction.guild_id)
        elif not is_server_up(interaction.guild.id) and get_server_info(interaction.guild.id).get("serverstarting"):
            await interaction.response.send_message("Let it finish starting, goddamn it")
            return
        else:
            command("stop", interaction.guild_id)
            update_server_info("up", 0, interaction.guild_id)
            await interaction.response.send_message(f"❌ {get_server_info(interaction.guild.id).get('serverid')} Server is now offline! ❌")
            #await self.bot.change_presence(
            #    activity=discord.Game("Server Offline ❌"),
            #)
            await interaction.response.send_message("Server stopped, now starting it again...")
            await startserver(self.bot, msg, interaction.guild_id)

    @app_commands.command(name="server", description="Select a server to set as Active")
    @app_commands.describe(server="Pick a server to set as active...")
    @app_commands.choices(
    server=[
        app_commands.Choice(name="-", value="check"),
        *[app_commands.Choice(name=server, value=server) for server in all_servers],
        ]
    )
    @has_mc_perm()
    async def server(self, interaction: discord.Interaction, server: app_commands.Choice[str]):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        serverid = get_server_info(interaction.guild.id).get("serverid")
        if server.value == "check":
            await interaction.response.send_message(f"Current server is set to: {serverid}")
            return
        else:
            if server.value not in config.get("guilds").get(str(interaction.guild.id)).get("ServerList"):
                await interaction.response.send_message(f"Server {server.value} is not in the list of servers for this guild, please only set servers that are allowed for this guild")
            update_server_info("serverid", server.value, interaction.guild.id)
            await interaction.response.send_message(f"Server has been changed to: {server.value}!")
            return

    @app_commands.command(name="ping", description="Responds \"Pong!\" - Used to test connection to the bot")
    async def ping(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        await interaction.response.send_message("Pong!")

    @app_commands.command(name="status", description="Responds with the current status of the active server")
    @has_mc_perm()
    async def status(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        await interaction.response.defer()
        message = await interaction.followup.send("Pinging server...", wait=True)
        if is_server_up(interaction.guild.id):
            update_server_info("serverstarting", 0, interaction.guild.id)
            #await self.bot.change_presence(
            #    activity=discord.Game(f"{get_server_info(interaction.guild.id).get("serverid")}✅"),
            #)
            await message.edit(content=f"✅ {get_server_info(interaction.guild.id).get('serverid')} Server is online! ✅")
        else:
            #await self.bot.change_presence(
            #    activity=discord.Game("Server Offline ❌"),
            #)
            await message.edit(content=f"❌ {get_server_info(interaction.guild.id).get('serverid')} Server is offline! ❌")

    @app_commands.command(name="list", description="Lists the current players on the active server")
    @has_mc_perm()
    async def list(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        if not is_server_up(interaction.guild.id):
            await interaction.response.send_message("Server isn't on")
            return
        await interaction.response.send_message(f"```{command('list', interaction.guild_id)}```")

    @app_commands.command(name="tps", description="Sends information regarding Ticks Per Second of the server (SkyFactory only)")
    @has_mc_perm()
    async def tps(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        if not is_server_up(interaction.guild.id):
            await interaction.response.send_message("Server isn't on")
            return
        if get_server_info(interaction.guild.id).get("serverid") != "SkyFactory5":
            await interaction.response.send_message(f"```{command('neoforge tps', interaction.guild_id)}```")
            return
        await interaction.response.send_message(f"```{command('forge tps', interaction.guild_id)}```")

    @app_commands.command(name="say", description="Says a message in minecraft chat")
    @has_mc_perm()
    async def say(self, interaction: discord.Interaction, message: str):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        if not is_server_up(interaction.guild.id):
            await interaction.response.send_message("Server isn't on")
            return
        fullmessage = f"say {message}"
        command(fullmessage)

    @app_commands.command(name="help", description="Gives information about possible commands")
    @has_mc_perm()
    async def help(self, interaction: discord.Interaction):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return

        await interaction.response.send_message("```\n"
                       "Commands:\n\n"
                       "/start                 - Start the server\n"
                       "/stop                  - Stop the server\n"
                       "/restart               - Restart the server\n"
                       "/server                - Changes the active server\n"
                       "/ping                  - Ping the bot\n"
                       "/status                - Check server status\n"
                       "/list                  - List players on the server\n"
                       "/tps                   - Get TPS of the server (20 tps is good, anything lower means laggy)\n"
                       "/say <message>         - Say a message in the server chat\n"

                       "/snoopiefact           - Get a random Snoopie fact in your server\n"
                       "/gemini <message>      - Ask Gemini anything!\n"

                       "/setmcpermsrole        - Set the role that can use the minecraft commands\n"
                       "/setmcconsolepermsrole - Set the role that can use the minecraft console commands\n"
                       "/setmcconsolechannel   - Set the channel for Minecraft console messages\n"
                       "/setmcchatchannel      - Set the channel for Minecraft chat messages\n"
                       "/setmcbotchannel       - Set the channel for the Minecraft bot messages\n"
                       "/setfactchannel        - Set the channel for Snoopie facts\n"
                       "/setfactrole           - Set the role to ping for Snoopie facts\n"
                       "/setpermsrole          - Set the role to have Snoopie fact permissions\n"
                       "/help                  - Show this message\n```\n")
                       
    async def cog_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send("❌ You don't have permission to use this command.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        else:
            print(f"Unhandled error: {error}")
    
async def setup(bot: commands.Bot):
    await bot.add_cog(YeetBot(bot))