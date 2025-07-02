import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from utils.data_manager import load_data
from utils.database import initialize_database # Make sure this import is at the top

# Load environment variables
load_dotenv()

# Define intents
intents = discord.Intents.default()
intents.members = True

# Subclass commands.Bot
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!#$%", intents=intents)

    async def setup_hook(self):
        """This is called once when the bot logs in to load cogs and sync commands."""
        
        # --- ADD THESE TWO LINES HERE ---
        load_data()
        initialize_database()
        
        print("Loading cogs...")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"-> Loaded cog: {filename}")
                except Exception as e:
                    print(f"-> Failed to load cog {filename}: {e}")
        
        await self.tree.sync() 
        print("Commands synced.")

    async def on_ready(self):
        # on_ready is now just for confirming the login
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print("Bot is ready and online.")


# Run the bot
bot = MyBot()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_BOT_TOKEN not found in .env file.")