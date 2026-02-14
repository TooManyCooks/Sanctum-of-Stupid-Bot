import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from PriorTracker import register_prior_tracker


def create_bot() -> commands.Bot:
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

    return bot


def run_bot() -> None:
    """Load configuration and start the Discord bot."""
    load_dotenv()
    token = os.getenv("discord_token")
    if not token:
        raise RuntimeError(
            "Missing discord_token. Set it in environment or a .env file before starting the bot."
        )

    handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
    bot = create_bot()
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)


if __name__ == "__main__":
    run_bot()
