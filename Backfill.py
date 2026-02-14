import re, datetime, discord
import asyncio, datetime, discord

async def backfill_text(bot, log_text_activity, text_data, save_json, TEXT_PATH, days: int = 14):
    cutoff = discord.utils.utcnow() - datetime.timedelta(days=days)
    for guild in bot.guilds:
        for ch in guild.text_channels:
            try:
                async for msg in ch.history(after=cutoff, oldest_first=True, limit=None):
                    if msg.author.bot or not msg.guild:
                        continue
                    await log_text_activity(msg, text_data)  # expects to save internally
                # if your logger does NOT save: uncomment next line
                # save_json(TEXT_PATH, text_data)
            except (discord.Forbidden, discord.HTTPException):
                pass  # no perms or fetch error; skip channel
            await asyncio.sleep(0)  # yield to event loop

JOIN_RE  = re.compile(r"<@!?(\d+)>.*joined voice channel", re.I)
LEAVE_RE = re.compile(r"<@!?(\d+)>.*left voice channel", re.I)

async def backfill_voice_from_log(interaction, channel_id: int, voice_data, save_json, VOICE_PATH, days: int = 14):
    await interaction.response.send_message("Backfilling voice from log…", ephemeral=True)
    ch = interaction.guild.get_channel(channel_id)
    if not ch or not isinstance(ch, discord.TextChannel):
        await interaction.followup.send("Invalid channel.", ephemeral=True)
        return

    cutoff = discord.utils.utcnow() - datetime.timedelta(days=days)
    gid_str = str(interaction.guild_id)

    try:
        async for msg in ch.history(after=cutoff, oldest_first=True, limit=None):
            ts = int(msg.created_at.timestamp())
            content = msg.content

            # pick the mentioned user that appears in the same line as the keyword if possible
            uid = None
            if msg.mentions:
                # simple heuristic: use the first mention; refine if your log has multiple mentions
                uid = str(msg.mentions[0].id)
            if uid is None:
                m = JOIN_RE.search(content) or LEAVE_RE.search(content)
                if m:
                    uid = m.group(1)
            if not uid:
                continue

            member  = interaction.guild.get_member(int(uid))
            display = member.display_name if member else uid
            g = voice_data.setdefault("users_by_guild", {}).setdefault(gid_str, {})
            u = g.setdefault(uid, {"display": display, "sessions": [], "_open": None})
            u["display"] = display

            if JOIN_RE.search(content):
                u["_open"] = ts
            elif LEAVE_RE.search(content):
                start = u.pop("_open", None)
                if isinstance(start, int) and ts >= start:
                    u["sessions"].append({"start": start, "end": ts})
    except (discord.Forbidden, discord.HTTPException):
        await interaction.followup.send("Cannot read that channel’s history.", ephemeral=True)
        return

    save_json(VOICE_PATH, voice_data)
    await interaction.followup.send("Voice backfill complete.", ephemeral=True)
