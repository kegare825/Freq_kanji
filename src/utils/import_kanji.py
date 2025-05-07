import json
import sqlite3
from pathlib import Path

def safe_int_convert(value):
    try:
        return int(value) if value.strip() else None
    except (ValueError, AttributeError):
        return None

def import_kanji_data():
    # Conectar a la base de datos
    conn = sqlite3.connect('data/kanji.db')
    cursor = conn.cursor()

    # Crear tabla si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kanji (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kanji TEXT NOT NULL,
        meaning TEXT,
        on_reading TEXT,
        kun_reading TEXT,
        strokes INTEGER,
        grade TEXT,
        jlpt TEXT,
        frequency INTEGER,
        unicode TEXT,
        examples TEXT
    )
    ''')

    # Leer el archivo JSON
    json_path = Path('data/kanji_data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        kanji_data = json.load(f)

    # Insertar datos
    for entry in kanji_data:
        kanji = entry['kanji']
        content = entry['content']
        
        # Extraer información del contenido
        meaning = None
        on_reading = None
        kun_reading = None
        strokes = None
        grade = None
        jlpt = None
        frequency = None
        unicode = None
        examples = None

        # Procesar el contenido línea por línea
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'es el kanji de' in line:
                meaning = line.split('es el kanji de')[1].strip()
            elif 'Lecturas chinas:' in line:
                on_reading = line.split(':')[1].strip()
            elif 'Lecturas japonesas:' in line:
                kun_reading = line.split(':')[1].strip()
            elif 'Trazos:' in line:
                strokes = safe_int_convert(line.split(':')[1])
            elif 'Grado:' in line:
                grade = line.split(':')[1].strip()
            elif 'JLPT:' in line:
                jlpt = line.split(':')[1].strip()
            elif 'Frecuencia' in line:
                freq = line.split('#')[1].strip()
                frequency = safe_int_convert(freq)
            elif 'Unicode:' in line:
                unicode = line.split(':')[1].strip()
            elif 'Palabras comunes' in line:
                # Recopilar ejemplos hasta encontrar "Palabras no comunes"
                examples = []
                j = i + 1
                while j < len(lines) and 'Palabras no comunes' not in lines[j]:
                    if lines[j].strip() and not lines[j].startswith('('):
                        examples.append(lines[j].strip())
                    j += 1
                examples = '\n'.join(examples) if examples else None

        # Insertar en la base de datos
        cursor.execute('''
        INSERT INTO kanji (kanji, meaning, on_reading, kun_reading, strokes, grade, jlpt, frequency, unicode, examples)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (kanji, meaning, on_reading, kun_reading, strokes, grade, jlpt, frequency, unicode, examples))

    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()

if __name__ == '__main__':
    import_kanji_data() 