import datetime
import json
import time
from pathlib import Path

import discord
from discord.ext import commands

ACTIVITY_REQ = 14  # days of activity to check
VOICE_LIMIT = 1  # hours needed
TEXT_LIMIT = 10  # messages needed

TEXT_TRACKER = Path("TextTracker.json")
VOICE_TRACKER = Path("VoiceTracker.json")


def load_json(path: Path) -> dict:
    """Load JSON safely and reset to {} if missing/invalid."""
    if not path.exists():
        path.write_text("{}", encoding="utf-8")
        return {}

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        path.write_text("{}", encoding="utf-8")
        return {}

    try:
        return json.loads(raw)
    except Exception:
        path.write_text("{}", encoding="utf-8")
        return {}


def save_json(path: Path, data: dict) -> None:
    """Save a dict to disk as pretty JSON."""
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_text_user(data: dict, guild_id: int, user_id: int, display: str) -> dict:
    gid = str(guild_id)
    uid = str(user_id)

    guild = data.setdefault("guilds", {}).setdefault(gid, {})
    users = guild.setdefault("users", {})
    user = users.setdefault(uid, {"display": display, "messages": []})
    user["display"] = display
    user.setdefault("messages", [])
    return user


def ensure_voice_user(data: dict, guild_id: int, user_id: int, display: str) -> dict:
    gid = str(guild_id)
    uid = str(user_id)

    guild = data.setdefault("guilds", {}).setdefault(gid, {})
    users = guild.setdefault("users", {})
    user = users.setdefault(uid, {
        "display": display,
        "sessions": [],
        "_open": None,
    })

    user["display"] = display
    user.setdefault("sessions", [])
    user.setdefault("_open", None)
    return user


def register_prior_tracker(bot: commands.Bot) -> None:
    """Attach prior-tracker listeners/commands to the bot instance."""
    text_data = load_json(TEXT_TRACKER)
    voice_data = load_json(VOICE_TRACKER)

    async def log_text_activity(message: discord.Message) -> bool:
        if message.author.bot or not message.guild:
            return False

        user = ensure_text_user(
            text_data,
            message.guild.id,
            message.author.id,
            message.author.display_name,
        )

        ts = int(message.created_at.timestamp())
        if ts in user["messages"]:
            return False

        user["messages"].append(ts)
        save_json(TEXT_TRACKER, text_data)
        return True

    async def log_voice_activity(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot or not member.guild:
            return

        user = ensure_voice_user(
            voice_data,
            member.guild.id,
            member.id,
            member.display_name,
        )

        now = int(time.time())
        joined = before.channel is None and after.channel is not None
        left = before.channel is not None and after.channel is None

        if joined:
            user["_open"] = now
            save_json(VOICE_TRACKER, voice_data)
        elif left:
            start = user.get("_open")
            user["_open"] = None
            if isinstance(start, int) and now >= start:
                user["sessions"].append({"start": start, "end": now})
                save_json(VOICE_TRACKER, voice_data)

    @bot.listen("on_message")
    async def prior_tracker_on_message(message: discord.Message):
        await log_text_activity(message)

    @bot.listen("on_voice_state_update")
    async def prior_tracker_on_voice_state_update(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        await log_voice_activity(member, before, after)

    @bot.command(name="backfill_text_log")
    @commands.has_permissions(administrator=True)
    async def backfill_text(ctx: commands.Context):
        """Backfill message activity for the last 14 days into TextTracker.json."""
        await ctx.send("Starting text backfill for the last 14 days...", delete_after=10)

        cutoff = discord.utils.utcnow() - datetime.timedelta(days=14)
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command can only be used in a server.", delete_after=10)
            return

        total_seen = 0
        total_logged = 0
        for channel in guild.text_channels:
            perms = channel.permissions_for(guild.me)
            if not perms.read_messages or not perms.read_message_history:
                continue

            try:
                async for msg in channel.history(after=cutoff, oldest_first=True, limit=None):
                    total_seen += 1
                    if await log_text_activity(msg):
                        total_logged += 1
            except (discord.Forbidden, discord.HTTPException):
                continue

        await ctx.send(
            f"Backfill complete.\n"
            f"Messages scanned: {total_seen}\n"
            f"Messages logged: {total_logged}",
            delete_after=30,
        )

    @backfill_text.error
    async def backfill_text_error(ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You need administrator permission to run this command.", delete_after=10)
            return
        raise error
