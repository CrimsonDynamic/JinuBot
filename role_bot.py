import discord
import os
import json
from dotenv import load_dotenv
from discord import app_commands
from discord.ui import Select, View
from datetime import datetime

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# --- CONFIGURATION & DATA HANDLING ---
DATA_FILE = "server_data.json"
SERVER_DATA = {}

def load_data():
    """Loads the main data object from the JSON file."""
    global SERVER_DATA
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                content = f.read()
                if content:
                    SERVER_DATA = json.loads(content)
                else:
                    SERVER_DATA = {}
        except (json.JSONDecodeError, IOError):
            SERVER_DATA = {}
    else:
        SERVER_DATA = {}

def save_data():
    """Saves the main data object to the JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(SERVER_DATA, f, indent=4)

def get_guild_data(guild_id: int) -> dict:
    """Gets the data for a specific guild, creating it if it doesn't exist."""
    guild_id_str = str(guild_id)
    if guild_id_str not in SERVER_DATA:
        SERVER_DATA[guild_id_str] = {
            "settings": {"log_channel": None},
            "roles": {}
        }
    return SERVER_DATA[guild_id_str]

# --- BOT SETUP ---
class MyBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        load_data()
        print(f"Managing data for {len(SERVER_DATA)} server(s).")
        await self.tree.sync()
        print('Commands synced globally!')

intents = discord.Intents.default()
intents.members = True
bot = MyBot(intents=intents)

# --- UI COMPONENTS ---
class RoleSelect(Select):
    def __init__(self, category: str, guild_id: int, user_roles):
        options = []
        guild_data = get_guild_data(guild_id)
        role_ids_in_category = guild_data["roles"].get(category, [])
        
        guild = bot.get_guild(guild_id)
        if guild:
            for role_id in role_ids_in_category:
                role = guild.get_role(int(role_id))
                if role:
                    description = "Click to get this role."
                    if role in user_roles:
                        description = "You already have this role. Click to remove."
                    options.append(discord.SelectOption(label=role.name, description=description, value=str(role.id)))

        super().__init__(placeholder=f"Select a role from '{category}'...", options=options, disabled=not options)

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        role = interaction.guild.get_role(int(self.values[0]))

        if role is None:
            await interaction.response.send_message("This role no longer exists.", ephemeral=True)
            return

        guild_data = get_guild_data(interaction.guild_id)
        log_channel_id = guild_data["settings"].get("log_channel")
        log_channel = bot.get_channel(log_channel_id) if log_channel_id else None

        try:
            action_text = ""
            embed_color = discord.Color.default()

            if role in member.roles:
                await member.remove_roles(role)
                await interaction.response.send_message(f"Role **{role.name}** removed.", ephemeral=True)
                action_text = f"**{member.mention} removed the role {role.mention}**"
                embed_color = discord.Color.orange()
            else:
                await member.add_roles(role)
                await interaction.response.send_message(f"Role **{role.name}** granted.", ephemeral=True)
                action_text = f"**{member.mention} received the role {role.mention}**"
                embed_color = discord.Color.green()

            if log_channel:
                embed = discord.Embed(
                    description=action_text,
                    color=embed_color,
                    timestamp=datetime.now()
                )
                embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
                await log_channel.send(embed=embed)

        except discord.Forbidden:
             await interaction.response.send_message("I don't have permission to manage that role! Make sure my role is higher.", ephemeral=True)
        except Exception as e:
            print(f"An error occurred in the role callback: {e}")

class CategorySelect(Select):
    def __init__(self, guild_id: int):
        guild_data = get_guild_data(guild_id)
        options = [discord.SelectOption(label=category) for category in guild_data["roles"].keys()]
        if not options:
             options.append(discord.SelectOption(label="No categories found", value="disabled"))
        super().__init__(placeholder="Choose a role category...", options=options, disabled=not guild_data["roles"])

    async def callback(self, interaction: discord.Interaction):
        chosen_category = self.values[0]
        if chosen_category == "disabled":
            await interaction.response.defer()
            return
            
        view = View(timeout=None)
        view.add_item(RoleSelect(category=chosen_category, guild_id=interaction.guild_id, user_roles=interaction.user.roles))
        await interaction.response.edit_message(content=f"Select a role from **{chosen_category}**:", view=view)

# --- USER COMMAND ---
@bot.tree.command(name="roles", description="Choose a role from a categorized menu!")
async def roles_command(interaction: discord.Interaction):
    guild_data = get_guild_data(interaction.guild_id)
    if not guild_data["roles"]:
        await interaction.response.send_message("No role categories have been configured for this server.", ephemeral=True)
        return

    view = View(timeout=None)
    view.add_item(CategorySelect(guild_id=interaction.guild_id))
    await interaction.response.send_message("Please select a category:", view=view, ephemeral=True)

# --- ADMIN COMMANDS ---
async def category_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    guild_data = get_guild_data(interaction.guild_id)
    return [
        app_commands.Choice(name=category, value=category)
        for category in guild_data["roles"] if current.lower() in category.lower()
    ]

@bot.tree.command(name="set_log_channel", description="Sets the channel for role activity logs.")
@app_commands.describe(channel="The channel to send logs to.")
@app_commands.checks.has_permissions(manage_guild=True)
async def set_log_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    guild_data = get_guild_data(interaction.guild_id)
    guild_data["settings"]["log_channel"] = channel.id
    save_data()
    await interaction.response.send_message(f"Log channel has been set to {channel.mention}.", ephemeral=True)

@bot.tree.command(name="add_category", description="Creates a new category for assignable roles.")
@app_commands.describe(category_name="The name for the new category (e.g., Game Roles)")
@app_commands.checks.has_permissions(manage_roles=True)
async def add_category(interaction: discord.Interaction, category_name: str):
    guild_data = get_guild_data(interaction.guild_id)
    if category_name in guild_data["roles"]:
        await interaction.response.send_message(f"A category named '{category_name}' already exists.", ephemeral=True)
    else:
        guild_data["roles"][category_name] = []
        save_data()
        await interaction.response.send_message(f"Category '{category_name}' has been created.", ephemeral=True)

@bot.tree.command(name="remove_category", description="Deletes a role category and all roles within it.")
@app_commands.describe(category_name="The category to delete")
@app_commands.autocomplete(category_name=category_autocomplete)
@app_commands.checks.has_permissions(manage_roles=True)
async def remove_category(interaction: discord.Interaction, category_name: str):
    guild_data = get_guild_data(interaction.guild_id)
    if category_name not in guild_data["roles"]:
        await interaction.response.send_message(f"No category named '{category_name}' found.", ephemeral=True)
    else:
        del guild_data["roles"][category_name]
        save_data()
        await interaction.response.send_message(f"Category '{category_name}' and all its roles have been removed.", ephemeral=True)

@bot.tree.command(name="add_role", description="Add a role to a specific category.")
@app_commands.describe(category="The category to add the role to", role="The role to add")
@app_commands.autocomplete(category=category_autocomplete)
@app_commands.checks.has_permissions(manage_roles=True)
async def add_role(interaction: discord.Interaction, category: str, role: discord.Role):
    guild_data = get_guild_data(interaction.guild_id)
    if category not in guild_data["roles"]:
        await interaction.response.send_message(f"The category '{category}' does not exist. Please create it first.", ephemeral=True)
        return

    role_id_str = str(role.id)
    if role_id_str in guild_data["roles"][category]:
        await interaction.response.send_message(f"The role **{role.name}** is already in the '{category}' category.", ephemeral=True)
    else:
        guild_data["roles"][category].append(role_id_str)
        save_data()
        await interaction.response.send_message(f"Successfully added **{role.name}** to the '{category}' category.", ephemeral=True)

@bot.tree.command(name="remove_role", description="Remove a role from a specific category.")
@app_commands.describe(category="The category to remove the role from", role="The role to remove")
@app_commands.autocomplete(category=category_autocomplete)
@app_commands.checks.has_permissions(manage_roles=True)
async def remove_role(interaction: discord.Interaction, category: str, role: discord.Role):
    guild_data = get_guild_data(interaction.guild_id)
    if category not in guild_data["roles"]:
        await interaction.response.send_message(f"The category '{category}' does not exist.", ephemeral=True)
        return
        
    role_id_str = str(role.id)
    if role_id_str not in guild_data["roles"][category]:
        await interaction.response.send_message(f"The role **{role.name}** is not in the '{category}' category.", ephemeral=True)
    else:
        guild_data["roles"][category].remove(role_id_str)
        save_data()
        await interaction.response.send_message(f"Successfully removed **{role.name}** from the '{category}' category.", ephemeral=True)

# --- RUN THE BOT ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if TOKEN is None:
    raise ValueError("DISCORD_BOT_TOKEN not found in .env file.")
bot.run(TOKEN)
