import json
import re
import sqlite3
from pathlib import Path

# Determinar la ruta base del proyecto
if __name__ == "__main__":
    # Si se ejecuta directamente, la ruta base es el directorio padre de src
    BASE_DIR = Path(__file__).parent.parent.parent
else:
    # Si se ejecuta como módulo, importar desde src.utils.paths
    from src.utils.paths import KANJI_JSON_PATH, KANJI_DB_PATH

# Definir rutas si se ejecuta directamente
if __name__ == "__main__":
    DATA_DIR = BASE_DIR / 'data'
    KANJI_JSON_PATH = DATA_DIR / 'kanji_data.json'
    KANJI_DB_PATH = DATA_DIR / 'kanji.db'
    DATA_DIR.mkdir(exist_ok=True)

def limpiar_lectura(texto):
    if not texto:
        return None
    # Eliminar todo lo que está entre paréntesis y después de '/'
    texto = re.sub(r'\([^)]*\)', '', texto)
    texto = re.sub(r'/.*$', '', texto)
    # Eliminar palabras en mayúsculas (lecturas occidentales)
    texto = re.sub(r'[A-Z]+', '', texto)
    # Limpiar espacios extra y caracteres especiales
    texto = re.sub(r'[,、]', '', texto)
    return texto.strip()

def clean_kanji_data():
    print("Iniciando limpieza de datos de kanji...")
    
    # Leer el archivo JSON
    with open(KANJI_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    print("\nExtrayendo significados y lecturas...")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(KANJI_DB_PATH)
    cursor = conn.cursor()
    
    # Crear tabla
    cursor.execute('DROP TABLE IF EXISTS kanji')
    cursor.execute('''
    CREATE TABLE kanji (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kanji TEXT UNIQUE NOT NULL,
        significado TEXT,
        lectura_china TEXT,
        lectura_japonesa TEXT
    )
    ''')
    
    # Procesar cada entrada
    for entry in data:
        content = entry.get("content", "")
        # Cortar a partir de la sección de palabras (marcada por "Palabras")
        cut_point = content.find("Palabras")
        if cut_point != -1:
            content = content[:cut_point].rstrip()
        
        lines = content.splitlines()

        # Extraer significado de la primera línea: "<kanji> es el kanji de <meaning>"
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

        # Extraer lecturas
        on, kun = None, None
        for i, ln in enumerate(lines):
            if "Lecturas chinas" in ln:
                # siguiente línea no vacía
                for x in lines[i+1:]:
                    if x.strip():
                        on = limpiar_lectura(x.strip())
                        break
            if "Lecturas japonesas" in ln:
                for x in lines[i+1:]:
                    if x.strip():
                        kun = limpiar_lectura(x.strip())
                        break

        # Insertar en la base de datos
        try:
            cursor.execute('''
            INSERT INTO kanji (kanji, significado, lectura_china, lectura_japonesa)
            VALUES (?, ?, ?, ?)
            ''', (entry["kanji"], meaning, on, kun))
        except sqlite3.IntegrityError:
            print(f"Advertencia: El kanji {entry['kanji']} ya existe en la base de datos")

    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()
    
    print(f"Proceso completado: {len(data)} kanji procesados")
    print(f"Datos guardados en {KANJI_DB_PATH}")

    # Guardar los datos limpios
    with open(KANJI_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("Limpieza completada.")

if __name__ == "__main__":
    clean_kanji_data() 