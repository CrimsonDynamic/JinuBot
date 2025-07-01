import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View
from datetime import datetime
from utils.data_manager import get_guild_data
from utils.log_manager import send_log # <-- Import the new log function

# --- UI Select Menus ---


class RoleSelectMenu(Select):
    def __init__(self, category: str, interaction: discord.Interaction):
        guild = interaction.guild
        user_roles = interaction.user.roles
        options = []
        
        guild_data = get_guild_data(guild.id)
        role_ids = guild_data["roles"].get(category, [])
        for role_id in role_ids:
            role = guild.get_role(int(role_id))
            if role:
                options.append(discord.SelectOption(
                    label=role.name,
                    value=str(role.id),
                    description="Select to add or remove this role."
                ))
        
        super().__init__(
            placeholder=f"Select one or more roles from '{category}'...",
            min_values=1,
            max_values=len(options) if options else 1,
            options=options,
            disabled=not options
        )

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        added_roles = []
        removed_roles = []

        # Loop through each selected role and sort it into an added/removed list
        for role_id in self.values:
            role = interaction.guild.get_role(int(role_id))
            if not role:
                continue

            if role in member.roles:
                await member.remove_roles(role)
                removed_roles.append(role)
            else:
                await member.add_roles(role)
                added_roles.append(role)
        
        # --- THIS IS THE CORRECTED LOGIC ---

        # 1. Create the confirmation message for the user
        response_lines = []
        if added_roles:
            response_lines.append(f"**Added:** {', '.join(r.mention for r in added_roles)}")
        if removed_roles:
            response_lines.append(f"**Removed:** {', '.join(r.mention for r in removed_roles)}")

        if not response_lines:
            await interaction.response.send_message("No changes were made.", ephemeral=True)
        else:
            await interaction.response.send_message("\n".join(response_lines), ephemeral=True)

        # 2. Create and send the log embed if any changes were made
        if added_roles or removed_roles:
            log_embed = discord.Embed(
                title="Role Update Log",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            log_embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            
            if added_roles:
                log_embed.add_field(name="Roles Added", value=', '.join(r.mention for r in added_roles), inline=False)
            if removed_roles:
                log_embed.add_field(name="Roles Removed", value=', '.join(r.mention for r in removed_roles), inline=False)

            await send_log(interaction, log_embed)
        
        # Stop the view since the action is complete
        self.view.stop()


class CategorySelectMenu(Select):
    def __init__(self, interaction: discord.Interaction):
        guild_data = get_guild_data(interaction.guild_id)
        options = [discord.SelectOption(label=category) for category in guild_data.get("roles", {})]
        if not options:
            options.append(discord.SelectOption(label="No categories found", value="disabled"))
        
        super().__init__(placeholder="Choose a role category...", options=options, disabled=not options)

    async def callback(self, interaction: discord.Interaction):
        chosen_category = self.values[0]
        if chosen_category == "disabled":
            await interaction.response.defer()
            return
            
        view = View(timeout=180.0)
        view.add_item(RoleSelectMenu(category=chosen_category, interaction=interaction))
        
        await interaction.response.edit_message(
            content=f"Now, select a role from the **{chosen_category}** category:", 
            view=view
        )

# --- The Main Cog Class ---

class UserCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="roles", description="Choose a role from a categorized menu!")
    async def roles(self, interaction: discord.Interaction):
        guild_data = get_guild_data(interaction.guild_id)
        if not guild_data.get("roles"):
            await interaction.response.send_message("No role categories have been configured for this server.", ephemeral=True)
            return
        
        # Create the initial view with the category selector
        view = View(timeout=180.0) 
        view.add_item(CategorySelectMenu(interaction=interaction))
        
        await interaction.response.send_message(
            "Please select a category:", 
            view=view, 
            ephemeral=True
        )

# Required setup function to load the cog
async def setup(bot: commands.Bot):
    await bot.add_cog(UserCommands(bot))
