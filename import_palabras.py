import sqlite3
import csv
import os

# Ruta a la base de datos
db_path = os.path.join('data', 'kanji.db')

# Ruta al CSV
csv_path = os.path.join('data', '5000_most_frequent_japanese_words.csv')

# Conectar a la base de datos
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Crear tabla de palabras frecuentes si no existe
cursor.execute('''
CREATE TABLE IF NOT EXISTS palabras_frecuentes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    frecuencia INTEGER,
    palabra TEXT,
    significado TEXT
)
''')

# Verificar si la tabla ya tiene datos
cursor.execute('SELECT COUNT(*) FROM palabras_frecuentes')
count = cursor.fetchone()[0]

# Si la tabla está vacía, insertar datos del CSV
if count == 0:
    # Leer el CSV y insertar datos
    with open(csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            cursor.execute(
                'INSERT INTO palabras_frecuentes (frecuencia, palabra, significado) VALUES (?, ?, ?)',
                (row['Frecuencia'], row['Palabra'], row['Significado'])
            )
    conn.commit()
    print(f"Datos importados correctamente a la tabla 'palabras_frecuentes'")
else:
    print(f"La tabla 'palabras_frecuentes' ya contiene {count} registros")

# Mostrar las 10 primeras filas de la tabla kanji
print("\n=== 10 PRIMERAS FILAS DE LA TABLA KANJI ===")
cursor.execute('SELECT * FROM kanji LIMIT 10')
for row in cursor.fetchall():
    print(row)

# Mostrar las 10 primeras filas de la tabla palabras_frecuentes
print("\n=== 10 PRIMERAS FILAS DE LA TABLA PALABRAS_FRECUENTES ===")
cursor.execute('SELECT * FROM palabras_frecuentes LIMIT 10')
for row in cursor.fetchall():
    print(row)

# Cerrar la conexión
conn.close() 