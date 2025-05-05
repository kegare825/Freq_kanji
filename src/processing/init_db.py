import sqlite3
import os
import json
from datetime import datetime

def init_db():
    """Inicializa la base de datos con las tablas necesarias."""
    # Obtener la ruta de la base de datos
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'kanji_data.db')
    
    # Conectar a la base de datos (la crea si no existe)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tabla de caracteres
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS characters (
        char TEXT PRIMARY KEY,
        meaning TEXT NOT NULL,
        aozora_freq REAL,
        news_freq REAL,
        wiki_freq REAL
    )
    ''')
    
    # Crear tabla de progreso SRS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS srs_progress (
        char TEXT PRIMARY KEY,
        next_review DATETIME,
        ease_factor REAL DEFAULT 2.5,
        interval INTEGER DEFAULT 0,
        repetitions INTEGER DEFAULT 0,
        FOREIGN KEY (char) REFERENCES characters(char)
    )
    ''')
    
    # Cargar datos desde el JSON si existe
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                            'data', 'kanji_meanings_readings.json')
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)
            
            # Insertar datos en la tabla characters
            for card in cards:
                cursor.execute('''
                INSERT OR IGNORE INTO characters (char, meaning)
                VALUES (?, ?)
                ''', (card['kanji'], card['meaning']))
            
            # Inicializar srs_progress para todos los caracteres
            cursor.execute('''
            INSERT OR IGNORE INTO srs_progress (char, next_review, ease_factor, interval, repetitions)
            SELECT char, ?, 2.5, 0, 0
            FROM characters
            ''', (datetime.now().isoformat(),))
    
    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()
    
    print(f"Base de datos inicializada en: {db_path}")

if __name__ == "__main__":
    init_db() 