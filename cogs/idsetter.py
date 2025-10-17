import os, discord
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from discord.app_commands import AppCommandError, CheckFailure
from utils.polling import *
from utils.utilities import *
from utils.perms import *

load_dotenv()

config = load_config()

class IDSetterBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setmcpermsrole", description="Set the role to be able to interact with the Minecraft Server")
    @is_admin()
    async def setmcpermsrole(self, interaction: discord.Interaction, role: discord.Role):
        config["guilds"][str(interaction.guild_id)]["mc_perms_role_id"] = role.id
        save_config(config)
        await interaction.response.send_message(f"Role <@&{role.id}> now has minecraft permissions!", ephemeral=True)

    @app_commands.command(name="setmcconsolepermsrole", description="Set the role to be able to interact with the Minecraft Server Console")
    @is_admin()
    async def setmcconsolepermsrole(self, interaction: discord.Interaction, role: discord.Role):
        config["guilds"][str(interaction.guild_id)]["mc_console_perms_role_id"] = role.id
        save_config(config)
        await interaction.response.send_message(f"Role <@&{role.id}> now has minecraft console permissions!", ephemeral=True)

    @app_commands.command(name="setmcconsolechannel", description="Set the channel for Minecraft chat")
    @has_mc_perm()
    async def setmcconsolechannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_console_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        config["guilds"][str(interaction.guild_id)]["mc_console_channel_id"] = channel.id
        save_config(config)
        await interaction.response.send_message(f"Channel {channel.name} will now be used for minecraft console!", ephemeral=True)

    @app_commands.command(name="setmcchatchannel", description="Set the channel for Minecraft chat")
    @has_mc_perm()
    async def setmcchatchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.channel_id != config.get("guilds").get(str(interaction.guild.id)).get("mc_bot_channel_id"):
            await interaction.response.send_message("This channel is not set up for this command", ephemeral=True)
            return
        config["guilds"][str(interaction.guild_id)]["mc_chat_channel_id"] = channel.id
        save_config(config)
        await interaction.response.send_message(f"Channel {channel.name} will now be used for minecraft chat!", ephemeral=True)

    @app_commands.command(name="setmcbotchannel", description="Set the channel for the Minecraft bot")
    @has_mc_perm()
    async def setmcbotchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config["guilds"][str(interaction.guild_id)]["mc_bot_channel_id"] = channel.id
        save_config(config)
        await interaction.response.send_message(f"Channel {channel.mention} will now be used for the minecraft bot!", ephemeral=True)
                       
    @app_commands.command(name="setfactchannel", description="Set the channel for Snoopie facts")
    @has_snoopie_perm()
    async def setfactchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = load_config()
        guild_id = str(interaction.guild.id)

        if "guilds" not in config:
            config["guilds"] = {}
        if guild_id not in config["guilds"]:
            config["guilds"][guild_id] = {}

        config["guilds"][guild_id]["snoopie_channel_id"] = channel.id
        save_config(config)

        await interaction.response.send_message(
            f"The channel <#{channel.id}> has been set for Facts!", ephemeral=True
        )

    @app_commands.command(name="setfactrole", description="Set the role to ping for Snoopie facts")
    @has_snoopie_perm()
    async def setfactrole(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        guild_id = str(interaction.guild.id)

        if "guilds" not in config:
            config["guilds"] = {}
        if guild_id not in config["guilds"]:
            config["guilds"][guild_id] = {}

        config["guilds"][guild_id]["snoopie_role_id"] = role.id
        save_config(config)

        await interaction.response.send_message(f"Role {role.name} will now be pinged!", ephemeral=True)

    @app_commands.command(name="setpermsrole", description="Set the role to be able to send Snoopie fact commands")
    @is_admin()
    async def setpermsrole(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        guild_id = str(interaction.guild.id)

        if "guilds" not in config:
            config["guilds"] = {}
        if guild_id not in config["guilds"]:
            config["guilds"][guild_id] = {}

        config["guilds"][guild_id]["snoopy_perms_role_id"] = role.id
        save_config(config)

        await interaction.response.send_message(f"Role <@&{role.id}> now has fact permissions!", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send("❌ You don't have permission to use this command.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        else:
            print(f"Unhandled error: {error}")
    
async def setup(bot: commands.Bot):
    await bot.add_cog(IDSetterBot(bot))