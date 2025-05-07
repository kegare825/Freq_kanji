"""
Script to initialize the SQLite database with the required tables.
"""
import os
import sys
import sqlite3
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.utils.config import DB_PATH, KANJI_DATA_PATH

def init_db():
    """Initialize the database with the required tables and data."""
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create the kanji table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kanji (
        kanji TEXT PRIMARY KEY,
        significado TEXT,
        lectura_china TEXT,
        lectura_japonesa TEXT
    )
    """)
    
    # Load data from JSON if it exists
    if os.path.exists(KANJI_DATA_PATH):
        with open(KANJI_DATA_PATH, 'r', encoding='utf-8') as f:
            kanji_data = json.load(f)
            
        # Insert or update kanji data
        for kanji, data in kanji_data.items():
            cursor.execute("""
            INSERT OR REPLACE INTO kanji (kanji, significado, lectura_china, lectura_japonesa)
            VALUES (?, ?, ?, ?)
            """, (
                kanji,
                data.get('meaning', ''),
                data.get('on_reading', ''),
                data.get('kun_reading', '')
            ))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db() 