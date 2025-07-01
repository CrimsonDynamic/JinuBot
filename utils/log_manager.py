import discord
from discord import Embed
from datetime import datetime
from .data_manager import get_guild_data

async def send_log(interaction: discord.Interaction, embed: discord.Embed):
    """A centralized function to send embeds to the server's log channel."""
    guild_data = get_guild_data(interaction.guild_id)
    log_channel_id = guild_data["settings"].get("log_channel")

    if not log_channel_id:
        return

    log_channel = interaction.client.get_channel(log_channel_id)
    if log_channel:
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            print(f"ERROR: Missing permissions to send to log channel {log_channel_id} in guild {interaction.guild_id}")
        except Exception as e:
            print(f"ERROR: Could not send log message: {e}")