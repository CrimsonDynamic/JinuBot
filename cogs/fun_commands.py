import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import aiohttp
import json
import random
import os

# --- HELPER FUNCTION TO SAVE QUESTIONS ---
QUESTIONS_FILE = "questions.json"

def add_question_to_library(question_type: str, rating: str, question: str):
    """Adds a new question to the local JSON file if it doesn't already exist."""
    if not os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, 'w') as f:
            json.dump({"truths": {"pg": [], "pg13": [], "r": []}, "dares": {"pg": [], "pg13": [], "r": []}}, f, indent=4)

    with open(QUESTIONS_FILE, 'r+') as f:
        try:
            data = json.load(f)
            if question_type not in data: data[question_type] = {}
            if rating not in data[question_type]: data[question_type][rating] = []
            
            if question not in data[question_type]:
                data[question_type][rating].append(question)
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
                print(f"Added new {question_type} to local library.")
        except (json.JSONDecodeError, KeyError):
            print("Error reading or updating questions.json.")


class FunCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Create a group named 'fun'
    fun = app_commands.Group(name="fun", description="A group of fun commands.")

    @fun.command(name="truth", description="Asks a random truth question.")
    @app_commands.describe(rating="Choose the rating of the question (defaults to random).")
    @app_commands.choices(rating=[
        Choice(name="PG", value="pg"),
        Choice(name="PG-13", value="pg13"),
        Choice(name="R", value="r"),
    ])
    async def truth(self, interaction: discord.Interaction, rating: Choice[str] = None):
        await interaction.response.defer()
        rating_value = rating.value if rating else random.choice(["pg", "pg13", "r"])
        api_url = f"https://api.truthordarebot.xyz/v1/truth?rating={rating_value}" # Corrected endpoint
        question_text = "Sorry, I couldn't fetch a question right now."
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        question_text = data.get("question", question_text)
                        # Add the fetched question to our local library
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

    @fun.command(name="dare", description="Gives a random dare from an API.")
    @app_commands.describe(rating="Choose the rating of the dare (defaults to random).")
    @app_commands.choices(rating=[
        Choice(name="PG", value="pg"),
        Choice(name="PG-13", value="pg13"),
        Choice(name="R", value="r"),
    ])
    async def dare(self, interaction: discord.Interaction, rating: Choice[str] = None):
        await interaction.response.defer()
        rating_value = rating.value if rating else random.choice(["pg", "pg13", "r"])
        api_url = f"https://api.truthordarebot.xyz/v1/dare?rating={rating_value}" # Corrected endpoint
        dare_text = "Sorry, I couldn't fetch a dare right now."

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        dare_text = data.get("question", dare_text)
                        # Add the fetched dare to our local library
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

    @fun.command(name="coinflip", description="Flips a coin.")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        color = discord.Color.gold() if result == "Heads" else discord.Color.dark_gray()
        embed = discord.Embed(
            title="Coin Flip",
            description=f"The coin landed on... **{result}**!",
            color=color
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="gif", description="Searches for a GIF on Tenor.")
    @app_commands.describe(search_term="What to search for")
    async def gif(self, interaction: discord.Interaction, search_term: str):
        await interaction.response.defer()
        tenor_api_key = os.getenv("TENOR_API_KEY")
        if not tenor_api_key:
            await interaction.followup.send("GIF command is not configured.")
            return

        url = f"https://tenor.googleapis.com/v2/search?q={search_term}&key={tenor_api_key}&limit=8"
        gif_url = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("results"):
                            gif_url = random.choice(data["results"])["media_formats"]["gif"]["url"]
        except Exception as e:
            print(f"Error fetching GIF: {e}")
        
        if gif_url:
            await interaction.followup.send(gif_url)
        else:
            await interaction.followup.send(f"Sorry, I couldn't find any GIFs for '{search_term}'.")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(FunCommands(bot))