# CS2 Update Tracker Bot 🔍

A Discord bot that automatically monitors and posts Counter-Strike 2 updates **before official patch notes are released** by tracking multiple sources.

## Features 🚀

- **Steam Depot Monitoring** - Detects new builds pushed to Steam (every 5 minutes)
- **Reddit Tracking** - Monitors r/GlobalOffensive for update posts (every 3 minutes)
- **Steam News** - Tracks official CS2 Steam news (every 10 minutes)
- **SteamDB Changes** - Watches database changes on SteamDB (every 15 minutes)
- **Instant Notifications** - Posts updates to Discord as soon as they're detected
- **Duplicate Prevention** - Tracks sent updates to avoid spam

## Installation 📦

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

3. Configure your `.env` file:
```
DISCORD_TOKEN=your_bot_token_here
UPDATE_CHANNEL_ID=your_channel_id_here
```

## Getting Bot Token 🔑

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the token and paste it in `.env`
5. Enable these intents:
   - Message Content Intent
   - Server Members Intent

## Getting Channel ID 📍

1. Enable Developer Mode in Discord (Settings > Advanced > Developer Mode)
2. Right-click on the channel where you want updates
3. Click "Copy Channel ID"
4. Paste it in `.env` as `UPDATE_CHANNEL_ID`

## Invite Bot to Server 🔗

Use this URL (replace YOUR_CLIENT_ID):
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2048&scope=bot
```

Required Permission: `Send Messages`

## Usage 🎮

### Run the bot:
```bash
python bot.py
```

### Commands:
- `!cs2 status` - Check monitoring status
- `!cs2 help` - Show help information

## How It Works 🔧

The bot monitors multiple sources:

1. **Steam Depot** - Checks for new build IDs on Steam's distribution system
2. **Reddit** - Scans r/GlobalOffensive for posts containing update keywords
3. **Steam News** - Monitors official CS2 news feed
4. **SteamDB** - Tracks database changes and modifications

When an update is detected, the bot:
- Creates an embed with update information
- Posts it to your configured Discord channel
- Saves the update hash to prevent duplicate notifications

## Update Detection Examples 📊

The bot can detect:
- ✅ New build versions before patch notes
- ✅ Depot updates and file changes
- ✅ Community-discovered updates on Reddit
- ✅ Official Valve announcements
- ✅ Database schema changes on SteamDB

## Data Storage 💾

The bot stores tracked updates in `tracked_updates.json` to prevent duplicate notifications.

## Configuration ⚙️

You can adjust monitoring intervals in `bot.py`:
- `check_steam_depot`: Default 5 minutes
- `check_reddit_updates`: Default 3 minutes
- `check_steam_news`: Default 10 minutes
- `check_steamdb`: Default 15 minutes

## Troubleshooting 🔧

**Bot not posting updates:**
- Verify `UPDATE_CHANNEL_ID` is correct
- Check bot has "Send Messages" permission in that channel
- Ensure bot token is valid

**Rate limit errors:**
- Increase task intervals if you get rate limited
- The default intervals are safe for most cases

## Credits 👏

Monitors data from:
- Steam Web API
- Reddit API
- SteamDB
- SteamCMD

## License 📄

MIT License - Feel free to modify and use!

---

Made with ❤️ for the CS2 community
