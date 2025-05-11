import sqlite3
import os

# Ruta a la base de datos
db_path = os.path.join('data', 'kanji.db')

# Conectar a la base de datos
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Obtener todas las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

# Mostrar las 10 primeras filas de cada tabla
for table in tables:
    table_name = table[0]
    print(f"\n=== TABLA: {table_name} ===")
    
    # Obtener nombres de columnas
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Columnas: {', '.join(columns)}\n")
    
    # Obtener datos
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
    rows = cursor.fetchall()
    
    if rows:
        for row in rows:
            print(row)
    else:
        print("(Tabla vacía)")
    
    print("-" * 50)

# Cerrar la conexión
conn.close()

print("\nConsulta completada.") 