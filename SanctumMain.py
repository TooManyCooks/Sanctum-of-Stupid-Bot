import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging

import time
import datetime
import tempfile

import json
from pathlib import Path

### Discord Bot Information
load_dotenv()
token = os.getenv("discord_token")
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix="/", intents=intents)

### Variables

activity_req = 14 # days of activity to check
voice_limit = 1 # hours needed 
text_limit = 10 # messages needed

### json portions
TEXT_TRACKER  = Path(r"C:\Users\trans\OneDrive\Desktop\Python Projects\Sanctum Bot Projects\SanctumRoleGiverV3\TextTracker.json")
VOICE_TRACKER = Path(r"C:\Users\trans\OneDrive\Desktop\Python Projects\Sanctum Bot Projects\SanctumRoleGiverV3\VoiceTracker.json")

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

text_data  = load_json(TEXT_TRACKER)
voice_data = load_json(VOICE_TRACKER)

def ensure_text_user(data: dict, guild_id: int, user_id: int, display: str) -> dict:
    gid = str(guild_id)
    uid = str(user_id)

    g = data.setdefault("guilds", {}).setdefault(gid, {})
    users = g.setdefault("users", {})
    user = users.setdefault(uid, {"display": display, "messages": []})
    # keep fields and display up to date
    user["display"] = display
    if "messages" not in user:
        user["messages"] = []

    return user

# log text activity
async def log_text_activity(message: discord.Message) -> None:
    if message.author.bot or not message.guild:
        return

    user = ensure_text_user(
        text_data,
        message.guild.id,
        message.author.id,
        message.author.display_name,
    )

    ts = int(message.created_at.timestamp())
    if ts in user["messages"]:
        return

    user["messages"].append(ts)
    save_json(TEXT_TRACKER, text_data)

# 
def ensure_voice_user(data: dict, guild_id: int, user_id: int, display: str) -> dict:
    gid = str(guild_id)
    uid = str(user_id)

    g = data.setdefault("guilds", {}).setdefault(gid, {})
    users = g.setdefault("users", {})
    user = users.setdefault(uid, {
        "display": display,
        "sessions": [],
        "_open": None,
    })

    # keep fields and display up to date
    user["display"] = display
    if "sessions" not in user:
        user["sessions"] = []
    if "_open" not in user:
        user["_open"] = None

    return user

# log voice activity
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
    left   = before.channel is not None and after.channel is None

    if joined:
        user["_open"] = now
        save_json(VOICE_TRACKER, voice_data)

    elif left:
        start = user.get("_open")
        user["_open"] = None

        if isinstance(start, int) and now >= start:
            user["sessions"].append({"start": start, "end": now})
            save_json(VOICE_TRACKER, voice_data)


### =====> Events

@bot.event
async def on_message(message: discord.Message):
    await log_text_activity(message)
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState,
):
    await log_voice_activity(member, before, after)


# =====> COMMANDS

# /SanctumHelp

# /check status
@bot.command()
async def check_status(ctx):
    """Reply with a simple status message."""
    await ctx.send(f'{bot.user.name} is online and connected to Discord')

# /backfill_text_log
@bot.command(name="backfill_text_log")
async def backfill_text(ctx: commands.Context):
    """
    Backfill message activity for the last 14 days into TextTracker.json.
    Admin-only.
    """
    await ctx.send("Starting text backfill for the last 14 days...", delete_after=10)

    # compute cutoff time
    cutoff = discord.utils.utcnow() - datetime.timedelta(days=14)

    guild = ctx.guild
    if guild is None:
        await ctx.send("This command can only be used in a server.", delete_after=10)
        return

    channels = list(guild.text_channels)
    total_seen = 0
    total_logged = 0

    for channel in channels:
        # skip channels we can't read
        if not channel.permissions_for(guild.me).read_messages:
            continue
        if not channel.permissions_for(guild.me).read_message_history:
            continue

        try:
            # oldest_first=True so events are in time order
            async for msg in channel.history(after=cutoff, oldest_first=True, limit=None):
                total_seen += 1
                # reuse your existing logger; it already ignores bots/DMs
                await log_text_activity(msg)
                total_logged += 1
        except (discord.Forbidden, discord.HTTPException):
            # no access or error; skip this channel
            continue

    await ctx.send(
        f"Backfill complete.\n"
        f"Messages scanned: {total_seen}\n"
        f"Messages logged: {total_logged}",
        delete_after=30
    )

### Execution Tree 

@bot.event
async def on_ready():
    print(f'{bot.user} is online and connected to Discord')

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
