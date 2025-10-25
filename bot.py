"""
CS2 Update Tracker Discord Bot
Monitors Counter-Strike 2 updates from multiple sources and posts them before official patch notes
"""

import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import re
import hashlib

load_dotenv()

# Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
UPDATE_CHANNEL_ID = int(os.getenv('UPDATE_CHANNEL_ID', 0))

class CS2UpdateBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        
        super().__init__(
            command_prefix='!cs2 ',
            intents=intents,
            help_command=None
        )
        
        self.session = None
        self.tracked_data = self.load_tracked_data()
        
    def load_tracked_data(self):
        """Load previously tracked update hashes"""
        try:
            with open('tracked_updates.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'steam_depot': {},
                'reddit_posts': [],
                'twitter_posts': [],
                'steam_news': [],
                'github_commits': []
            }
    
    def save_tracked_data(self):
        """Save tracked update hashes"""
        with open('tracked_updates.json', 'w') as f:
            json.dump(self.tracked_data, f, indent=2)
    
    async def setup_hook(self):
        """Initialize the bot"""
        self.session = aiohttp.ClientSession()
        print("🔍 CS2 Update Tracker Bot Starting...")
        
        # Start monitoring tasks
        self.check_steam_depot.start()
        self.check_steam_news.start()
        self.check_steamdb.start()
        
    async def close(self):
        """Cleanup on bot shutdown"""
        if self.session:
            await self.session.close()
        await super().close()
    
    async def on_ready(self):
        """Called when bot is ready"""
        print(f'✅ Bot Online: {self.user.name}')
        print(f'📊 Monitoring CS2 updates in {len(self.guilds)} server(s)')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="CS2 Updates 🔍"
            )
        )
    
    async def send_update(self, embed):
        """Send update to configured channel"""
        if UPDATE_CHANNEL_ID:
            try:
                channel = self.get_channel(UPDATE_CHANNEL_ID)
                if channel:
                    await channel.send(embed=embed)
                    print(f"✅ Sent update to channel: {channel.name}")
            except Exception as e:
                print(f"❌ Error sending update: {e}")
    
    @tasks.loop(minutes=5)
    async def check_steam_depot(self):
        """Check Steam Depot for CS2 updates"""
        try:
            # SteamDB API - CS2 App ID: 730
            url = "https://api.steamcmd.net/v1/info/730"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data and '730' in data['data']:
                        depot_info = data['data']['730']
                        current_hash = hashlib.md5(
                            json.dumps(depot_info, sort_keys=True).encode()
                        ).hexdigest()
                        
                        # Check if this is a new update
                        if current_hash != self.tracked_data['steam_depot'].get('last_hash'):
                            build_id = depot_info.get('depots', {}).get('branches', {}).get('public', {}).get('buildid', 'Unknown')
                            
                            embed = discord.Embed(
                                title="🚨 CS2 Steam Depot Update Detected!",
                                description="A new build has been pushed to Steam",
                                color=0xFF6B00,
                                timestamp=datetime.utcnow()
                            )
                            embed.add_field(name="Build ID", value=f"`{build_id}`", inline=True)
                            embed.add_field(name="App ID", value="730 (CS2)", inline=True)
                            embed.add_field(
                                name="ℹ️ Info",
                                value="This update was detected through Steam's depot system. Patch notes may follow soon.",
                                inline=False
                            )
                            embed.set_footer(text="CS2 Update Tracker • SteamDB Monitor")
                            
                            await self.send_update(embed)
                            
                            self.tracked_data['steam_depot']['last_hash'] = current_hash
                            self.tracked_data['steam_depot']['last_build'] = build_id
                            self.save_tracked_data()
                            
        except Exception as e:
            print(f"❌ Error checking Steam Depot: {e}")
    
    @tasks.loop(minutes=10)
    async def check_steam_news(self):
        """Check Steam News for CS2 announcements"""
        try:
            url = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=730&count=5&format=json"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('appnews', {}).get('newsitems', []):
                        news_id = str(item['gid'])
                        
                        if news_id not in self.tracked_data['steam_news']:
                            embed = discord.Embed(
                                title="📰 Official CS2 Steam News",
                                description=item['title'],
                                url=item['url'],
                                color=0x1B2838,
                                timestamp=datetime.fromtimestamp(item['date'])
                            )
                            
                            # Clean and truncate contents
                            contents = re.sub(r'\[.*?\]', '', item.get('contents', ''))
                            contents = re.sub(r'<.*?>', '', contents)
                            contents = contents[:500]
                            
                            if contents:
                                embed.add_field(name="Summary", value=contents, inline=False)
                            
                            embed.add_field(name="Author", value=item.get('author', 'Valve'), inline=True)
                            embed.set_footer(text="CS2 Update Tracker • Steam News")
                            
                            await self.send_update(embed)
                            self.tracked_data['steam_news'].append(news_id)
                            
                            # Keep only last 50 tracked news
                            if len(self.tracked_data['steam_news']) > 50:
                                self.tracked_data['steam_news'] = self.tracked_data['steam_news'][-50:]
                            
                            self.save_tracked_data()
                            
        except Exception as e:
            print(f"❌ Error checking Steam News: {e}")
    
    @tasks.loop(minutes=15)
    async def check_steamdb(self):
        """Check SteamDB changes page"""
        try:
            # This monitors the SteamDB changes feed
            url = "https://steamdb.info/api/GetAppHistoryItems/"
            
            params = {
                'appid': 730,
                'itemsPerPage': 5
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process SteamDB changes
                    for change in data.get('data', [])[:3]:
                        change_id = str(change.get('ChangeID', ''))
                        
                        if change_id and change_id not in self.tracked_data.get('steamdb_changes', []):
                            embed = discord.Embed(
                                title="🔧 SteamDB: CS2 Database Change",
                                description="A change has been detected in CS2's Steam database",
                                url=f"https://steamdb.info/app/730/history/",
                                color=0x2A3F5F,
                                timestamp=datetime.utcnow()
                            )
                            
                            embed.add_field(name="Change ID", value=f"`{change_id}`", inline=True)
                            embed.add_field(name="Type", value=change.get('Type', 'Unknown'), inline=True)
                            embed.set_footer(text="CS2 Update Tracker • SteamDB Monitor")
                            
                            await self.send_update(embed)
                            
                            if 'steamdb_changes' not in self.tracked_data:
                                self.tracked_data['steamdb_changes'] = []
                            
                            self.tracked_data['steamdb_changes'].append(change_id)
                            
                            # Keep only last 50
                            if len(self.tracked_data['steamdb_changes']) > 50:
                                self.tracked_data['steamdb_changes'] = self.tracked_data['steamdb_changes'][-50:]
                            
                            self.save_tracked_data()
                            
        except Exception as e:
            print(f"❌ Error checking SteamDB: {e}")
    
    @check_steam_depot.before_loop
    @check_steam_news.before_loop
    @check_steamdb.before_loop
    async def before_tasks(self):
        """Wait until bot is ready before starting tasks"""
        await self.wait_until_ready()

# Commands
@commands.command(name='status')
async def status(ctx):
    """Check bot monitoring status"""
    embed = discord.Embed(
        title="🔍 CS2 Update Tracker Status",
        description="Currently monitoring multiple sources for CS2 updates",
        color=0x00FF00
    )
    
    embed.add_field(name="✅ Steam Depot", value="Every 5 minutes", inline=True)
    embed.add_field(name="✅ Steam News", value="Every 10 minutes", inline=True)
    embed.add_field(name="✅ SteamDB", value="Every 15 minutes", inline=True)
    
    embed.set_footer(text=f"Monitoring since: {ctx.bot.user.created_at.strftime('%Y-%m-%d')}")
    
    await ctx.send(embed=embed)

@commands.command(name='help')
async def help_command(ctx):
    """Show help information"""
    embed = discord.Embed(
        title="📚 CS2 Update Tracker Help",
        description="Automatically tracks CS2 updates from multiple sources",
        color=0x5865F2
    )
    
    embed.add_field(
        name="🔍 Monitored Sources",
        value="• Steam Depot (Build Updates)\n• Steam Official News\n• SteamDB Changes",
        inline=False
    )
    
    embed.add_field(
        name="📝 Commands",
        value="`!cs2 status` - Check monitoring status\n`!cs2 help` - Show this help message",
        inline=False
    )
    
    embed.add_field(
        name="ℹ️ How it works",
        value="The bot checks various sources every few minutes and posts updates as soon as they're detected, often before official patch notes are released!",
        inline=False
    )
    
    await ctx.send(embed=embed)

# Initialize and run bot
if __name__ == "__main__":
    bot = CS2UpdateBot()
    bot.add_command(status)
    bot.add_command(help_command)
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
