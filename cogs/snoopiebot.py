import discord, os
from discord.ext import commands, tasks
from dotenv import load_dotenv
from discord import app_commands
from discord.app_commands import AppCommandError, CheckFailure
from utils.utilities import *
from utils.perms import has_snoopie_perm, is_admin

load_dotenv()

introprompt = r"You are a fact expert writing in the style of Snapple facts. Generate a true, interesting, and surprising fact in a short, friendly tone. Make sure it is accurate, easy to understand, and sounds like it could be printed under a bottle cap. Use clear and concise wording, no more than 1–2 sentences. Begin the fact directly, like: “Did you know...” or “Honey never spoils...” Avoid common facts, urban legends, or anything misleading or unverified. Double-check that it is scientifically or historically correct."
categorization = "Describe the fact in as few words as possible, such as \"flamingo group name\" for talking about a flamboyant of flamingos, or \"temperature of lightning\""
consistantcopies = "Flamingo group name, temperature of lightning, Owl group name, snail sleep duration, ketchup medicine, holding nose prevents humming, eiffel tower thermal expansion, shortest war, venus day duration"

class SnoopieBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.send_daily_fact.start()

    def cog_unload(self):
        self.send_daily_fact.cancel()

    @tasks.loop(hours=24)
    async def send_daily_fact(self):
        await self.bot.wait_until_ready()
        await self.send_fact()

    async def send_fact(self, server: int | None = None):
        config = load_config()
        guilds = config.get("guilds", {})
        previous_facts = get_facts()

        fact = ask_gemini(f"{introprompt}\n\nDo not make it about the following facts:{previous_facts} {consistantcopies}")
        topic = ask_gemini(f"{categorization} {fact}")
        set_random_fact(topic)

        if server:
            guilds = {str(server): guilds.get(str(server), {})}
        print(f"Sending fact: {fact} to guilds: {guilds.keys()}")

        for guild_id, data in list(guilds.items()):

            guild_obj = self.bot.get_guild(int(guild_id))
            if guild_obj is None:
                print(f"[{guild_id}] Bot is no longer in that guild; pruning from config.")
                guilds.pop(guild_id, None)
                continue
            
            channel_id = data.get("snoopie_channel_id")
            role_id = data.get("snoopie_role_id")

            if channel_id == 1 or role_id == 1:
                print(f"[{guild_id}] missing channel/role")
                continue

            print(f"Sending fact to guild {guild_id} in channel {channel_id} with role {role_id}")
            if channel_id and role_id:
                print("fetching channel...")
                channel = await self.bot.fetch_channel(channel_id)
                if channel:
                    print(f"Sending fact to channel {channel_id} in guild {guild_id}")
                    await channel.send(f"<@&{role_id}> 🌞 Snoopie Fact:\n**{fact}**")
        save_config(config)

    @send_daily_fact.before_loop
    async def before_send(self):
        await wait_until_10am()
        print("Daily fact loop is starting...")

    @app_commands.command(name="snoopiefact", description="Gets a random Snoopie fact")
    @has_snoopie_perm()
    async def snoopiefact(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Snoopiefact on the way!", ephemeral=True)
        await self.send_fact(interaction.guild.id)

    @app_commands.command(name="gemini", description="Ask Gemini anything!")
    @has_snoopie_perm()
    async def gemini(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        status_msg = await interaction.followup.send("Asking Gemini...", wait=True)
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, ask_gemini, message)

        chunks = []
        max_len = 2000
        text = response

        while len(text) > max_len:
            cutoff = text.rfind('.', 0, max_len)
            if cutoff == -1:
                cutoff = max_len

            chunks.append(text[:cutoff+1].strip())
            text = text[cutoff+1:].strip()

        if len(chunks) < 3 and text:
            chunks.append(text)
        elif len(text) > 0:
            chunks.append("Message too long, message trimmed")

        await status_msg.edit(content=chunks[0])

        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)

    @app_commands.command(name="sendallsnoopiefact", description="Gets a random Snoopie fact")
    @is_admin()
    async def sendallsnoopiefact(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Snoopiefacts moving down the pipelines!", ephemeral=True)
        await self.send_fact()
        
    async def cog_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        print("handled inside cog")
        if isinstance(error, CheckFailure):
            if interaction.response.is_done():
                await interaction.followup.send("❌ You don't have permission to use this command.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
        else:
            print(f"Unhandled error: {error}")

async def setup(bot: commands.Bot):
    await bot.add_cog(SnoopieBot(bot))