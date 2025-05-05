import json
import re
import os
import logging
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_meaning(lines):
    """Extrae el significado del kanji de las líneas de texto."""
    # Intentar extraer de la primera línea: "<kanji> es el kanji de <meaning>"
    meaning = None
    m = re.match(r".*es el kanji de (.+)", lines[0])
    if m:
        meaning = m.group(1).strip()
    else:
        # fallback: tomar la segunda non-empty line
        for ln in lines[1:]:
            if ln.strip():
                meaning = ln.strip()
                break
    return meaning

def extract_readings(lines):
    """Extrae las lecturas on y kun del kanji."""
    on, kun = None, None
    for i, ln in enumerate(lines):
        if "Lecturas chinas" in ln:
            # siguiente línea no vacía
            for x in lines[i+1:]:
                if x.strip():
                    on = x.strip()
                    break
        if "Lecturas japonesas" in ln:
            for x in lines[i+1:]:
                if x.strip():
                    kun = x.strip()
                    break
    return on, kun

def init_database(db_path):
    """Inicializa la base de datos SQLite con la tabla necesaria."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Crear tabla si no existe
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS kanji_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kanji TEXT UNIQUE NOT NULL,
            meaning TEXT,
            on_reading TEXT,
            kun_reading TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise

def save_to_database(conn, kanji_data):
    """Guarda los datos procesados en la base de datos."""
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        for entry in kanji_data:
            cursor.execute('''
            INSERT OR REPLACE INTO kanji_data 
            (kanji, meaning, on_reading, kun_reading, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                entry['kanji'],
                entry['meaning'],
                entry['lecturas_chinas'],
                entry['lecturas_japonesas'],
                now
            ))
        
        conn.commit()
        logger.info(f"Guardados {len(kanji_data)} registros en la base de datos")
    except sqlite3.Error as e:
        logger.error(f"Error al guardar en la base de datos: {e}")
        raise

def show_first_10_records(db_path):
    """Muestra los primeros 10 registros de la base de datos."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT kanji, meaning, on_reading, kun_reading
        FROM kanji_data
        ORDER BY id
        LIMIT 10
        ''')
        
        records = cursor.fetchall()
        
        print("\nPrimeros 10 registros de la base de datos:")
        print("-" * 80)
        print(f"{'Kanji':<6} {'Significado':<30} {'On-yomi':<15} {'Kun-yomi':<15}")
        print("-" * 80)
        
        for record in records:
            kanji, meaning, on_reading, kun_reading = record
            print(f"{kanji:<6} {meaning:<30} {on_reading or 'N/A':<15} {kun_reading or 'N/A':<15}")
        
        print("-" * 80)
        conn.close()
        
    except sqlite3.Error as e:
        logger.error(f"Error al leer de la base de datos: {e}")
        raise

def process_kanji_data():
    """Procesa el archivo JSON de datos de kanji y extrae significados y lecturas."""
    try:
        # Obtener rutas de archivos
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        input_path = os.path.join(data_dir, 'kanji_data.json')
        output_path = os.path.join(data_dir, 'kanji_meanings_readings.json')
        db_path = os.path.join(data_dir, 'kanji_data.db')

        # Cargar datos
        logger.info(f"Cargando datos desde {input_path}")
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)

        # Procesar cada entrada
        output = []
        for entry in data:
            text = entry.get("content", "")
            lines = text.splitlines()

            meaning = extract_meaning(lines)
            on, kun = extract_readings(lines)

            output.append({
                "kanji": entry["kanji"],
                "meaning": meaning,
                "lecturas_chinas": on,
                "lecturas_japonesas": kun
            })

        # Guardar resultado en JSON
        logger.info(f"Guardando resultados en {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        # Guardar en base de datos
        logger.info(f"Inicializando base de datos en {db_path}")
        conn = init_database(db_path)
        save_to_database(conn, output)
        conn.close()

        # Mostrar primeros 10 registros
        show_first_10_records(db_path)

        logger.info(f"Procesamiento completado. {len(output)} entradas generadas.")
        return True

    except FileNotFoundError as e:
        logger.error(f"No se encontró el archivo: {e}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}")
        return False
    except sqlite3.Error as e:
        logger.error(f"Error en la base de datos: {e}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    process_kanji_data()