import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import aiohttp
import json
import random
import os

QUESTIONS_FILE = "questions.json"

# CHANGED: The helper function now takes a 'question_type' argument
def add_question_to_library(question_type: str, rating: str, question: str):
    """Adds a new question to the local JSON file under the correct type and rating."""
    if not os.path.exists(QUESTIONS_FILE):
        # Create a default structure if the file is missing
        with open(QUESTIONS_FILE, 'w') as f:
            json.dump({"truths": {"pg": [], "pg13": [], "r": []}, "dares": {"pg": [], "pg13": [], "r": []}}, f, indent=4)

    with open(QUESTIONS_FILE, 'r+') as f:
        try:
            data = json.load(f)
            
            # Ensure the top-level type (truths/dares) exists
            if question_type not in data:
                data[question_type] = {}
            # Ensure the rating category exists within the type
            if rating not in data[question_type]:
                data[question_type][rating] = []
            
            # Add the question if it's not already in the specific list
            if question not in data[question_type][rating]:
                data[question_type][rating].append(question)
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                print(f"Added new {question_type} to local library: {question}")
        except (json.JSONDecodeError, KeyError):
            print("Error reading or updating questions.json, file might be corrupted or have an old format.")

class FunCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="truth", description="Asks a random truth question.")
    @app_commands.describe(rating="Choose the rating of the question (defaults to random).")
    @app_commands.choices(rating=[
        Choice(name="PG (Clean)", value="pg"),
        Choice(name="PG-13 (Teens)", value="pg13"),
        Choice(name="R (NSFW-ish)", value="r"),
    ])
    async def truth(self, interaction: discord.Interaction, rating: Choice[str] = None):
        await interaction.response.defer()
        rating_value = rating.value if rating else random.choice(["pg", "pg13", "r"])
        api_url = f"https://api.truthordarebot.xyz/v1/truth?rating={rating_value}"
        question_text = "Sorry, I couldn't fetch a question right now."
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        question_text = data.get("question", question_text)
                        # CHANGED: Pass "truths" as the type
                        add_question_to_library("truths", rating_value, question_text)
        except Exception as e:
            print(f"An error occurred during API request: {e}")

        color_map = {"pg": discord.Color.green(), "pg13": discord.Color.blue(), "r": discord.Color.red()}
        embed = discord.Embed(
            title=f" Truth ({rating_value.upper()})",
            description=f"## {question_text}",
            color=color_map.get(rating_value, discord.Color.purple())
        )
        embed.set_footer(text=f"Question for {interaction.user.display_name}", icon_url=self.bot.user.avatar.url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="dare", description="Gives a random dare from an API.")
    @app_commands.describe(rating="Choose the rating of the dare (defaults to random).")
    @app_commands.choices(rating=[
        Choice(name="PG (Safe)", value="pg"),
        Choice(name="PG-13 (Silly)", value="pg13"),
        Choice(name="R (Intense)", value="r"),
    ])
    async def dare(self, interaction: discord.Interaction, rating: Choice[str] = None):
        await interaction.response.defer()
        rating_value = rating.value if rating else random.choice(["pg", "pg13", "r"])
        api_url = f"https://api.truthordarebot.xyz/v1/dare?rating={rating_value}"
        dare_text = "Sorry, I couldn't fetch a dare right now."

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        dare_text = data.get("question", dare_text)
                        # CHANGED: Pass "dares" as the type
                        add_question_to_library("dares", rating_value, dare_text)
        except Exception as e:
            print(f"An error occurred during API request: {e}")

        color_map = {"pg": 0x3498db, "pg13": 0xf1c40f, "r": 0x992d22}
        embed = discord.Embed(
            title=f" Dare ({rating_value.upper()})",
            description=f"## {dare_text}",
            color=color_map.get(rating_value, 0x2ecc71)
        )
        embed.set_footer(text=f"Dare for {interaction.user.display_name}", icon_url=self.bot.user.avatar.url)
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="coinflip", description="Flips a coin and shows the result.")
    async def coinflip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="Coin Flip Result",
            description=f"**{result}**",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Flipped by {interaction.user.display_name}", icon_url=self.bot.user.avatar.url)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(FunCommands(bot))