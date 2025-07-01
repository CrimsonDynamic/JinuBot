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
                is_selected = role in user_roles
                options.append(discord.SelectOption(
                    label=role.name,
                    value=str(role.id),
                    description=f"Click to {'remove' if is_selected else 'get'} this role."
                ))
        
        super().__init__(placeholder=f"Select a role from '{category}'...", options=options, disabled=not options)

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)

        if not role:
            await interaction.response.send_message("That role no longer exists.", ephemeral=True)
            return

        # This logic is now updated to use the centralized logger
        try:
            if role in member.roles:
                await member.remove_roles(role)
                await interaction.response.send_message(f"Role **{role.name}** has been removed.", ephemeral=True)
                # Create and send the log embed
                log_embed = discord.Embed(description=f"**{member.mention} removed the role {role.mention}**", color=discord.Color.orange(), timestamp=datetime.now())
                log_embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
                await send_log(interaction, log_embed)
            else:
                await member.add_roles(role)
                await interaction.response.send_message(f"Role **{role.name}** has been granted.", ephemeral=True)
                # Create and send the log embed
                log_embed = discord.Embed(description=f"**{member.mention} received the role {role.mention}**", color=discord.Color.green(), timestamp=datetime.now())
                log_embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
                await send_log(interaction, log_embed)
        except discord.Forbidden:
            await interaction.response.send_message("I do not have permissions to manage this role.", ephemeral=True)
        
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