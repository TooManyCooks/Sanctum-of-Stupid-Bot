# Sanctum-of-Stupid-Bot

Discord activity tracker bot with text and voice tracking plus admin-only text backfill.

## How To Run

1. Create a virtual environment:
   `python -m venv .venv`
2. Activate the virtual environment:
   PowerShell: `.venv\Scripts\Activate.ps1`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Create your environment file:
   copy `.env.example` to `.env` and set real values.
5. Start the bot:
   `python SanctumMain.py`

## Environment Variables

- `discord_token`: Discord bot token
- `discord_guild_id`: Numeric guild/server ID

## Commands

- `!check_status`
- `!backfill_text_log` (administrator permission required)

## Discord Developer Portal Intents

Enable these intents for your bot application:

- Message Content Intent
- Server Members Intent
- Voice State Intent
