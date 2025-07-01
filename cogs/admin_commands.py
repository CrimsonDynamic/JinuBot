import discord
from discord.ext import commands
from discord import app_commands
from utils.data_manager import get_guild_data, save_data

# --- Autocomplete Function ---
# This helper function provides suggestions for the 'category' parameter in commands.
async def category_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    guild_data = get_guild_data(interaction.guild_id)
    # Return a list of choices where the category name includes the user's current input
    return [
        app_commands.Choice(name=category, value=category)
        for category in guild_data.get("roles", {}) if current.lower() in category.lower()
    ]

# --- The Main Cog Class for Admin Commands ---

class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="set_log_channel", description="Sets the channel for role activity logs.")
    @app_commands.describe(channel="The channel to send logs to.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_data = get_guild_data(interaction.guild_id)
        guild_data["settings"]["log_channel"] = channel.id
        save_data()
        await interaction.response.send_message(f"Log channel has been set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="add_category", description="Creates a new category for assignable roles.")
    @app_commands.describe(category_name="The name for the new category (e.g., Game Roles)")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def add_category(self, interaction: discord.Interaction, category_name: str):
        guild_data = get_guild_data(interaction.guild_id)
        roles_data = guild_data.setdefault("roles", {})
        if category_name in roles_data:
            await interaction.response.send_message(f"A category named '{category_name}' already exists.", ephemeral=True)
        else:
            roles_data[category_name] = []
            save_data()
            await interaction.response.send_message(f"Category '{category_name}' has been created.", ephemeral=True)

    @app_commands.command(name="remove_category", description="Deletes a role category and all roles within it.")
    @app_commands.describe(category_name="The category to delete")
    @app_commands.autocomplete(category_name=category_autocomplete)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def remove_category(self, interaction: discord.Interaction, category_name: str):
        guild_data = get_guild_data(interaction.guild_id)
        roles_data = guild_data.get("roles", {})
        if category_name not in roles_data:
            await interaction.response.send_message(f"No category named '{category_name}' found.", ephemeral=True)
        else:
            del roles_data[category_name]
            save_data()
            await interaction.response.send_message(f"Category '{category_name}' and all its roles have been removed.", ephemeral=True)

    @app_commands.command(name="add_role", description="Adds a role to a specific category.")
    @app_commands.describe(category="The category to add the role to", role="The role to add")
    @app_commands.autocomplete(category=category_autocomplete)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def add_role(self, interaction: discord.Interaction, category: str, role: discord.Role):
        guild_data = get_guild_data(interaction.guild_id)
        roles_data = guild_data.get("roles", {})
        if category not in roles_data:
            await interaction.response.send_message(f"The category '{category}' does not exist. Please create it first.", ephemeral=True)
            return

        role_id_str = str(role.id)
        if role_id_str in roles_data[category]:
            await interaction.response.send_message(f"The role **{role.name}** is already in the '{category}' category.", ephemeral=True)
        else:
            roles_data[category].append(role_id_str)
            save_data()
            await interaction.response.send_message(f"Successfully added **{role.name}** to the '{category}' category.", ephemeral=True)

    @app_commands.command(name="remove_role", description="Removes a role from a specific category.")
    @app_commands.describe(category="The category to remove the role from", role="The role to remove")
    @app_commands.autocomplete(category=category_autocomplete)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def remove_role(self, interaction: discord.Interaction, category: str, role: discord.Role):
        guild_data = get_guild_data(interaction.guild_id)
        roles_data = guild_data.get("roles", {})
        if category not in roles_data:
            await interaction.response.send_message(f"The category '{category}' does not exist.", ephemeral=True)
            return
        
        role_id_str = str(role.id)
        if role_id_str not in roles_data[category]:
            await interaction.response.send_message(f"The role **{role.name}** is not in the '{category}' category.", ephemeral=True)
        else:
            roles_data[category].remove(role_id_str)
            save_data()
            await interaction.response.send_message(f"Successfully removed **{role.name}** from the '{category}' category.", ephemeral=True)
    
    @app_commands.command(name="setup_roles", description="Posts an instructional message for the /roles command.")
    @app_commands.describe(channel="The channel where the instructional message will be sent.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_roles(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Creates the roles setup message."""
        
        embed = discord.Embed(
            title="✨ Role Selection ✨",
            description="Welcome! You can get your roles here by using the `/roles` command.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="How to use it:",
            value=(
                "1. Type `/roles` in any channel.\n"
                "2. A private menu will appear. First, select a category.\n"
                "3. A second menu will appear with all the roles for that category.\n"
                "4. **You can select multiple roles at once!** The bot will add any roles you select that you don't have, and remove any you select that you already have."
            ),
            inline=False
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(text="Your roles are managed here.")

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"Successfully sent the roles setup message to {channel.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send messages in that channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)

# Required setup function that the bot runs to load this cog
async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCommands(bot))