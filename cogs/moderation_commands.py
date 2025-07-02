import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from utils.database import get_db_connection
from utils.log_manager import send_log
import uuid # <-- Import the UUID library

class ModerationCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="warn", description="Warns a user and records the incident.")
    @app_commands.describe(user="The user to warn", reason="The reason for the warning")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        await interaction.response.defer(ephemeral=True)

        # Generate a UUID for the warning
        warning_id = str(uuid.uuid4())

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO warnings (warning_id, guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)",
            (warning_id, interaction.guild_id, user.id, interaction.user.id, reason)
        )
        conn.commit()
        conn.close()

        # Create the confirmation embed using the shortened UUID
        mod_embed = discord.Embed(
            title="✅ User Warned",
            description=f"**Warning ID:** `{warning_id[:8]}`",
            color=discord.Color.orange()
        )
        mod_embed.add_field(name="User", value=user.mention, inline=True)
        mod_embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        mod_embed.add_field(name="Reason", value=reason, inline=False)
        mod_embed.set_thumbnail(url=user.display_avatar.url)

        # Log the action
        log_embed = discord.Embed(
            title="Moderation Log: User Warned",
            color=discord.Color.dark_orange(),
            timestamp=datetime.now()
        )
        log_embed.add_field(name="Warned User", value=f"{user.mention} (`{user.id}`)", inline=False)
        log_embed.add_field(name="Moderator", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
        log_embed.add_field(name="Reason", value=reason, inline=False)
        log_embed.set_footer(text=f"Warning ID: {warning_id[:8]}")
        await send_log(interaction, log_embed)
        
        try:
            dm_embed = discord.Embed(title=f"You have received a warning in {interaction.guild.name}", description=f"**Reason:** {reason}", color=discord.Color.orange())
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            mod_embed.set_footer(text="Note: Could not send a DM to the user.")

        await interaction.followup.send(embed=mod_embed)

    @app_commands.command(name="warnings", description="Checks the warning history of a user.")
    @app_commands.describe(user="The user whose warnings you want to see")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        conn = get_db_connection()
        user_warnings = conn.execute(
            "SELECT warning_id, moderator_id, reason, timestamp FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC",
            (interaction.guild_id, user.id)
        ).fetchall()
        conn.close()

        if not user_warnings:
            await interaction.followup.send(f"{user.display_name} has a clean record.", ephemeral=True)
            return

        embed = discord.Embed(title=f"Warning History for {user.display_name}", color=discord.Color.yellow())
        embed.set_thumbnail(url=user.display_avatar.url)

        for warning in user_warnings:
            mod = self.bot.get_user(warning['moderator_id']) or f"ID: {warning['moderator_id']}"
            mod_name = mod.name if isinstance(mod, discord.User) else mod
            warn_time = datetime.strptime(warning['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            # Display the shortened UUID
            embed.add_field(
                name=f"ID: `{warning['warning_id'][:8]}` on {warn_time}",
                value=f"**Reason:** {warning['reason']}\n**Moderator:** {mod_name}",
                inline=False
            )
        await interaction.followup.send(embed=embed)

    # ...
    
    @app_commands.command(name="remove_warning", description="Removes a warning by the start of its ID.")
    @app_commands.describe(warning_id="The first 8 characters of the warning ID")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def remove_warning(self, interaction: discord.Interaction, warning_id: str):
        await interaction.response.defer(ephemeral=True)
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Find the warning details *before* deleting it
        cursor.execute("SELECT user_id, reason FROM warnings WHERE warning_id LIKE ? AND guild_id = ?", (f"{warning_id}%", interaction.guild_id))
        warning_to_delete = cursor.fetchone()

        if not warning_to_delete:
            await interaction.followup.send(f"Could not find a warning with an ID starting with `{warning_id}`.", ephemeral=True)
            conn.close()
            return

        # Step 2: Now that we have the details, delete the warning
        cursor.execute("DELETE FROM warnings WHERE warning_id LIKE ? AND guild_id = ?", (f"{warning_id}%", interaction.guild_id))
        conn.commit()
        conn.close()

        # Step 3: Send a confirmation to the moderator
        await interaction.followup.send(f"Warning starting with ID `{warning_id}` has been deleted.", ephemeral=True)

        # Step 4: Log the action
        warned_user = self.bot.get_user(warning_to_delete['user_id']) or f"ID: {warning_to_delete['user_id']}"
        warned_user_mention = warned_user.mention if isinstance(warned_user, discord.User) else warned_user

        log_embed = discord.Embed(
            title="Moderation Log: Warning Removed",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        log_embed.add_field(name="Removed Warning Starting With ID", value=f"`{warning_id}`", inline=False)
        log_embed.add_field(name="Original User", value=warned_user_mention, inline=False)
        log_embed.add_field(name="Original Reason", value=warning_to_delete['reason'], inline=False)
        log_embed.add_field(name="Action By", value=interaction.user.mention, inline=False)
        
        # Use our centralized logging function
        await send_log(interaction, log_embed)
async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCommands(bot))