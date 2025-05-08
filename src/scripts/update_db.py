import sqlite3
import pandas as pd
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
KANJI_DB_PATH = DATA_DIR / 'kanji.db'
CSV_PATH = DATA_DIR / 'kanji_combined.csv'

def alter_table():
    """Añade las nuevas columnas a la tabla kanji"""
    conn = sqlite3.connect(KANJI_DB_PATH)
    cursor = conn.cursor()
    
    # Nuevas columnas a añadir
    new_columns = [
        'aozora_char_count INTEGER',
        'news_char_count INTEGER',
        'wiki_char_count INTEGER',
        'aozora_doc_count INTEGER',
        'news_doc_count INTEGER',
        'wiki_doc_count INTEGER',
        'total_char_count INTEGER',
        'total_doc_count INTEGER',
        'aozora_char_freq REAL',
        'news_char_freq REAL',
        'wiki_char_freq REAL',
        'aozora_doc_freq REAL',
        'news_doc_freq REAL',
        'wiki_doc_freq REAL',
        'total_char_freq REAL',
        'total_doc_freq REAL'
    ]
    
    # Añadir cada columna si no existe
    for column in new_columns:
        column_name = column.split()[0]
        try:
            cursor.execute(f"ALTER TABLE kanji ADD COLUMN {column}")
            print(f"Columna {column_name} añadida")
        except sqlite3.OperationalError:
            print(f"Columna {column_name} ya existe")
    
    conn.commit()
    conn.close()

def update_database():
    """Actualiza la base de datos con la información del CSV"""
    # Leer el CSV
    df = pd.read_csv(CSV_PATH)
    
    # Conectar a la base de datos
    conn = sqlite3.connect(KANJI_DB_PATH)
    cursor = conn.cursor()
    
    # Actualizar cada kanji
    for _, row in df.iterrows():
        update_query = """
        UPDATE kanji SET 
            aozora_char_count = ?,
            news_char_count = ?,
            wiki_char_count = ?,
            aozora_doc_count = ?,
            news_doc_count = ?,
            wiki_doc_count = ?,
            total_char_count = ?,
            total_doc_count = ?,
            aozora_char_freq = ?,
            news_char_freq = ?,
            wiki_char_freq = ?,
            aozora_doc_freq = ?,
            news_doc_freq = ?,
            wiki_doc_freq = ?,
            total_char_freq = ?,
            total_doc_freq = ?
        WHERE kanji = ?
        """
        
        cursor.execute(update_query, (
            row['aozora_char_count'],
            row['news_char_count'],
            row['wiki_char_count'],
            row['aozora_doc_count'],
            row['news_doc_count'],
            row['wiki_doc_count'],
            row['total_char_count'],
            row['total_doc_count'],
            row['aozora_char_freq'],
            row['news_char_freq'],
            row['wiki_char_freq'],
            row['aozora_doc_freq'],
            row['news_doc_freq'],
            row['wiki_doc_freq'],
            row['total_char_freq'],
            row['total_doc_freq'],
            row['char']
        ))
        
        # Imprimir progreso
        if _ % 100 == 0:
            print(f"Procesados {_} registros...")
    
    conn.commit()
    conn.close()
    print("Base de datos actualizada correctamente")

def main():
    print("Modificando la estructura de la tabla...")
    alter_table()
    print("\nActualizando datos...")
    update_database()
    print("\nProceso completado")

if __name__ == "__main__":
    main() 