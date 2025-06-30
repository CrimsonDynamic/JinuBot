import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import aiohttp
import random

class FunCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="truth", description="Asks a random truth question from an API.")
    @app_commands.describe(rating="Choose the rating of the question (defaults to PG).")
    @app_commands.choices(rating=[
        Choice(name="PG (Clean questions, for everyone)", value="pg"),
        Choice(name="PG-13 (Teen-focused questions)", value="pg13"),
        Choice(name="R (NSFW-ish questions, 18+)", value="r"),
    ])
    async def truth(self, interaction: discord.Interaction, rating: Choice[str] = None):
        await interaction.response.defer()
        if rating:
            rating_value = rating.value
        else:
            # If no rating is chosen, pick one randomly
            rating_value = random.choice(["pg", "pg13", "r"])

        api_url = f"https://api.truthordarebot.xyz/v1/truth?rating={rating_value}"
        question_text = "Sorry, I couldn't fetch a question right now. Please try again later."
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        question_text = data.get("question", question_text)
        except Exception as e:
            print(f"An error occurred during API request: {e}")

        color_map = {"pg": discord.Color.green(), "pg13": discord.Color.blue(), "r": discord.Color.red()}
        embed_color = color_map.get(rating_value, discord.Color.purple())

        embed = discord.Embed(
            title=f"🤔 Truth ({rating_value.upper()})",
            description=f"## {question_text}",
            color=embed_color
        )
        embed.set_footer(text=f"Question for {interaction.user.display_name}", icon_url=self.bot.user.avatar.url)
        await interaction.followup.send(embed=embed)

    # --- NEW DARE COMMAND ---
    @app_commands.command(name="dare", description="Gives a random dare from an API.")
    @app_commands.describe(rating="Choose the rating of the dare (defaults to PG).")
    @app_commands.choices(rating=[
        Choice(name="PG (Safe dares, for everyone)", value="pg"),
        Choice(name="PG-13 (Silly dares, for teens)", value="pg13"),
        Choice(name="R (Intense dares, 18+)", value="r"),
    ])
    async def dare(self, interaction: discord.Interaction, rating: Choice[str] = None):
        await interaction.response.defer()
        if rating:
            rating_value = rating.value
        else:
            # If no rating is chosen, pick one randomly
            rating_value = random.choice(["pg", "pg13", "r"])
        # The only change is using the 'dare' endpoint instead of 'truth'
        api_url = f"https://api.truthordarebot.xyz/v1/dare?rating={rating_value}"
        dare_text = "Sorry, I couldn't fetch a dare right now. Please try again later."

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        dare_text = data.get("question", dare_text)
        except Exception as e:
            print(f"An error occurred during API request: {e}")

        color_map = {"pg": 0x3498db, "pg13": 0xf1c40f, "r": 0x992d22} # Different colors for dares
        embed_color = color_map.get(rating_value, 0x2ecc71)

        embed = discord.Embed(
            title=f" Dare ({rating_value.upper()})",
            description=f"## {dare_text}",
            color=embed_color
        )
        embed.set_footer(text=f"Dare for {interaction.user.display_name}", icon_url=self.bot.user.avatar.url)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(FunCommands(bot))