import sqlite3
from .paths import KANJI_DB_PATH

def init_db():
    # Conectar a la base de datos
    conn = sqlite3.connect(KANJI_DB_PATH)
    cursor = conn.cursor()

    # Eliminar la tabla si existe
    cursor.execute('DROP TABLE IF EXISTS kanji')

    # Crear tabla con las columnas específicas
    cursor.execute('''
    CREATE TABLE kanji (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kanji TEXT NOT NULL,
        meaning TEXT,
        lecturas_japonesas TEXT,
        lecturas_chinas TEXT
    )
    ''')

    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Base de datos inicializada correctamente con el nuevo esquema.") 