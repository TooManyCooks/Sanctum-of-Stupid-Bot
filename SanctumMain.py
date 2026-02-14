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
        guild = bot.get_guild(int(bot.target_guild_id)) if bot.target_guild_id else None
        if guild:
            print(f"{bot.user} is online and connected to guild: {guild.name} ({guild.id})")
        else:
            print(f"{bot.user} is online and connected to Discord")

    return bot


def _resolve_runtime_settings() -> tuple[str, str]:
    """Resolve token and guild id from environment variables."""
    load_dotenv()

    token = os.getenv("discord_token")
    guild_id = os.getenv("discord_guild_id")

    if not token:
        raise RuntimeError("Missing discord_token environment variable.")

    if not guild_id:
        raise RuntimeError("Missing discord_guild_id environment variable.")

    try:
        int(guild_id)
    except ValueError as exc:
        raise RuntimeError("Guild ID must be a numeric Discord guild ID.") from exc

    return token, guild_id


def run_bot() -> None:
    """Load configuration and start the Discord bot."""
    token, guild_id = _resolve_runtime_settings()

    handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
    bot = create_bot()
    # attach configured guild id for lightweight ready-time diagnostics
    bot.target_guild_id = guild_id  # type: ignore[attr-defined]
    bot.run(token, log_handler=handler, log_level=logging.INFO)


if __name__ == "__main__":
    run_bot()
