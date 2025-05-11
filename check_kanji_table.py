import sqlite3
import os

# Ruta a la base de datos
db_path = os.path.join('data', 'kanji.db')

# Conectar a la base de datos
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar si la tabla kanji existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kanji'")
if cursor.fetchone():
    # Contar los registros en la tabla kanji
    cursor.execute("SELECT COUNT(*) FROM kanji")
    count = cursor.fetchone()[0]
    print(f"La tabla 'kanji' contiene {count} registros")
    
    # Mostrar la estructura de la tabla kanji
    print("\n=== ESTRUCTURA DE LA TABLA KANJI ===")
    cursor.execute("PRAGMA table_info(kanji)")
    for col in cursor.fetchall():
        print(f"Columna {col[0]}: {col[1]} ({col[2]})")
    
    # Si hay registros, mostrar los primeros 10
    if count > 0:
        print("\n=== PRIMEROS 10 REGISTROS DE LA TABLA KANJI ===")
        cursor.execute("SELECT * FROM kanji LIMIT 10")
        for row in cursor.fetchall():
            print(row)
    else:
        print("\nLa tabla 'kanji' está vacía")
else:
    print("La tabla 'kanji' no existe en la base de datos")

# Cerrar la conexión
conn.close() 