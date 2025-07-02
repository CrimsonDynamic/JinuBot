import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, TextStyle
from utils.data_manager import get_guild_data, save_data
from utils.database import get_db_connection
import uuid

# --- The Modal (Pop-up Form) ---
class ConfessionModal(ui.Modal, title="Submit an Anonymous Confession"):
    confession_text = ui.TextInput(
        label="Your Confession",
        style=TextStyle.paragraph,
        placeholder="Type your confession here... No one will know it was you.",
        required=True,
        max_length=1000,
    )

    async def on_submit(self, interaction: Interaction):
        """This runs when the user hits the 'Submit' button."""
        guild_data = get_guild_data(interaction.guild_id)
        confession_channel_id = guild_data["settings"].get("confession_channel")

        if not confession_channel_id:
            await interaction.response.send_message("The confession channel has not been set up.", ephemeral=True)
            return

        confession_channel = interaction.client.get_channel(confession_channel_id)
        if not confession_channel:
            await interaction.response.send_message("I can't find the configured confession channel.", ephemeral=True)
            return

        confession_id = str(uuid.uuid4())

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO confessions (confession_id, guild_id, user_id, content) VALUES (?, ?, ?, ?)",
            (confession_id, interaction.guild_id, interaction.user.id, self.confession_text.value)
        )
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="New Anonymous Confession",
            description=self.confession_text.value,
            color=discord.Color.from_rgb(47, 49, 54)
        )
        embed.set_footer(text=f"Confession ID: {confession_id[:8]}")
        
        try:
            await confession_channel.send(embed=embed)
            await interaction.response.send_message("Your confession has been posted anonymously! ✅", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I can't post in the confessions channel.", ephemeral=True)


# --- The Main Cog Class ---
class Confessions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="set_confession_channel", description="Sets the channel where anonymous confessions will be posted.")
    @app_commands.describe(channel="The channel for confessions.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_confession_channel(self, interaction: Interaction, channel: discord.TextChannel):
        guild_data = get_guild_data(interaction.guild_id)
        guild_data["settings"]["confession_channel"] = channel.id
        save_data()
        await interaction.response.send_message(f"Confession channel has been set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="delete_confession", description="Admin only: Deletes a confession by its ID.")
    @app_commands.describe(confession_id="The first 8 characters of the confession ID")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def delete_confession(self, interaction: discord.Interaction, confession_id: str):
        await interaction.response.defer(ephemeral=True)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # --- THIS IS THE FIX ---
        # Use LIKE to match the start of the UUID.
        cursor.execute("DELETE FROM confessions WHERE confession_id LIKE ? AND guild_id = ?", (f"{confession_id}%", interaction.guild_id))
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if rows_deleted > 0:
            await interaction.followup.send(f"Confession starting with ID `{confession_id}` has been successfully deleted.", ephemeral=True)
        else:
            await interaction.followup.send(f"Could not find a confession with an ID starting with `{confession_id}`.", ephemeral=True)

    @app_commands.command(name="confess", description="Submit a confession anonymously.")
    async def confess(self, interaction: Interaction):
        modal = ConfessionModal()
        await interaction.response.send_modal(modal)

# --- CORRECTED SETUP FUNCTION ---
async def setup(bot: commands.Bot): # Changed GearsBot to Bot
    await bot.add_cog(Confessions(bot))