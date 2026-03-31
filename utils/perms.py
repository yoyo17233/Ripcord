import discord, os
from discord.app_commands import CheckFailure
from discord import app_commands
from utils.data import containers, get_containerid_from_interaction, get_containerid_from_channelid
from utils.networking import is_server_up

VERBOSE = True

SUPERUSERS = os.getenv("SUPERUSERS")
superusers = [int(x) for x in SUPERUSERS.split(",") if x.strip()]

def has_bot_perm():
    return app_commands.check(check_bot_perm)

async def check_bot_perm(interaction: discord.Interaction) -> bool:
    containerid = get_containerid_from_interaction(interaction)
    if containerid == None:
        raise CheckFailure("No container associated with this channel.")
    bot_perm = containers[containerid]["bot_perm"]
    member = interaction.user
    if any(role.id == bot_perm for role in member.roles):
        return True
    role = interaction.guild.get_role(bot_perm)
    role_name = role.name if role else f"ID {bot_perm}"
    raise CheckFailure(f'User does not have required role: {role_name}')

def has_console_perm():
    return app_commands.check(check_console_perm)

def check_console_perm(interaction: discord.Interaction) -> bool:
    containerid = get_containerid_from_interaction(interaction)
    if containerid == None:
        raise CheckFailure("No container associated with this channel.")
    console_perm = containers[containerid]["console_perm"]
    member = interaction.user
    if any(role.id == console_perm for role in member.roles):
        return True
    role = interaction.guild.get_role(console_perm)
    role_name = role.name if role else f"ID {console_perm}"
    raise CheckFailure(f'User does not have required role: {role_name}')

def check_console_perm_msg(message: discord.Message) -> bool:
    containerid = get_containerid_from_channelid(message.channel.id)
    if containerid == None:
        raise CheckFailure("No container associated with this channel.")
    console_perm = containers[containerid]["console_perm"]
    member = message.author
    if any(role.id == console_perm for role in member.roles):
        return True
    role = message.guild.get_role(console_perm)
    role_name = role.name if role else f"ID {console_perm}"
    raise CheckFailure(f'User does not have required role: {role_name}')

def is_admin():
    async def predicate(interaction) -> bool:
        if interaction.permissions.administrator:
            return True
        raise CheckFailure("You must be an Administrator to use this command.")
    return app_commands.check(predicate)

def is_superuser():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id in superusers:
            return True
        else:
            raise CheckFailure("You don't have permission to use this command.")
    return app_commands.check(predicate)

def check_is_admin(interaction: discord.Interaction) -> bool:
    if interaction.permissions.administrator:
        return True
    return False
    
def check_is_superuser(interaction: discord.Interaction) -> bool:
    if interaction.user in superusers:
        return True
    return False

def check_is_server_up():
    return app_commands.check(server_up)

def server_up(interaction: discord.Interaction) -> bool:
    container_id = get_containerid_from_interaction(interaction)
    if is_server_up(container_id):
        return True
    raise CheckFailure(f"{containers[container_id]["server"]} server is down")

def is_bot_channel():
    return app_commands.check(check_is_bot_channel)

def check_is_bot_channel(interaction: discord.Interaction) -> bool:
    container_id = get_containerid_from_interaction(interaction)
    channel_id = interaction.channel_id
    bot_channel_id = containers[container_id]["bot_channel_id"]
    if bot_channel_id == channel_id:
        return True
    raise CheckFailure(f"<#{channel_id}> is not the botchannel for its container. Try <#{bot_channel_id}>")