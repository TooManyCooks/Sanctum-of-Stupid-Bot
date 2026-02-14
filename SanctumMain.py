import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from PriorTracker import register_prior_tracker

### Discord Bot Information
load_dotenv()
token = os.getenv("discord_token")
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Register modular features
register_prior_tracker(bot)


@bot.command()
async def check_status(ctx):
    """Reply with a simple status message."""
    await ctx.send(f"{bot.user.name} is online and connected to Discord")


@bot.event
async def on_ready():
    print(f"{bot.user} is online and connected to Discord")


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
