import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from utils.data_manager import load_data

# Load environment variables
load_dotenv()

# Define intents
intents = discord.Intents.default()
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        # A command prefix is not needed for a slash-command-only bot
        super().__init__(command_prefix="!#$%", intents=intents)

    async def setup_hook(self):
        """This is called once when the bot logs in to load cogs and sync commands."""
        print("Loading cogs...")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"-> Loaded cog: {filename}")
                except Exception as e:
                    print(f"-> Failed to load cog {filename}: {e}")
        
        # Sync all commands to Discord
        await self.tree.sync() 
        print("Commands synced.")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        load_data()
        print("Data loaded.")

# Run the bot
bot = MyBot()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_BOT_TOKEN not found in .env file.")