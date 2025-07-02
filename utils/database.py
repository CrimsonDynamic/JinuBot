import sqlite3

DATABASE_FILE = "database.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Creates the necessary tables if they don't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # --- UPDATED WARNINGS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            warning_id TEXT PRIMARY KEY, -- Changed from INTEGER to TEXT
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
     # --- UPDATED CONFESSIONS TABLE ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS confessions (
            confession_id TEXT PRIMARY KEY, -- Changed from INTEGER to TEXT
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")