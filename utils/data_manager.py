import os
import json

DATA_FILE = "server_data.json"
SERVER_DATA = {}

def load_data():
    global SERVER_DATA
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            content = f.read()
            SERVER_DATA = json.loads(content) if content else {}
    else:
        SERVER_DATA = {}

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(SERVER_DATA, f, indent=4)

def get_guild_data(guild_id: int) -> dict:
    """Retrieve or initialize data for a specific guild."""
    guild_id_str = str(guild_id)
    if guild_id_str not in SERVER_DATA:
        SERVER_DATA[guild_id_str] = {
            "settings": {"log_channel": None},
            "roles": {}
        }
    return SERVER_DATA[guild_id_str]