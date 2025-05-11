import sqlite3
import os

# Ruta a la base de datos
db_path = os.path.join('data', 'kanji.db')

# Datos básicos de kanji 
basic_kanji_data = [
    {"kanji": "日", "significado": "sol, día", "lectura_china": "ニチ, ジツ", "lectura_japonesa": "ひ, -び, -か"},
    {"kanji": "一", "significado": "uno", "lectura_china": "イチ, イツ", "lectura_japonesa": "ひと-"},
    {"kanji": "国", "significado": "país, nación", "lectura_china": "コク", "lectura_japonesa": "くに"},
    {"kanji": "人", "significado": "persona", "lectura_china": "ジン, ニン", "lectura_japonesa": "ひと"},
    {"kanji": "年", "significado": "año", "lectura_china": "ネン", "lectura_japonesa": "とし"},
    {"kanji": "大", "significado": "grande", "lectura_china": "ダイ, タイ", "lectura_japonesa": "おお-"},
    {"kanji": "本", "significado": "libro, origen", "lectura_china": "ホン", "lectura_japonesa": "もと"},
    {"kanji": "中", "significado": "medio, dentro", "lectura_china": "チュウ", "lectura_japonesa": "なか"},
    {"kanji": "長", "significado": "largo, jefe", "lectura_china": "チョウ", "lectura_japonesa": "なが-"},
    {"kanji": "出", "significado": "salir", "lectura_china": "シュツ, スイ", "lectura_japonesa": "で-る"},
    {"kanji": "三", "significado": "tres", "lectura_china": "サン", "lectura_japonesa": "み-"},
    {"kanji": "時", "significado": "tiempo, hora", "lectura_china": "ジ", "lectura_japonesa": "とき"},
    {"kanji": "行", "significado": "ir", "lectura_china": "コウ, ギョウ, アン", "lectura_japonesa": "い-く"},
    {"kanji": "見", "significado": "ver", "lectura_china": "ケン", "lectura_japonesa": "み-る"},
    {"kanji": "月", "significado": "mes, luna", "lectura_china": "ゲツ, ガツ", "lectura_japonesa": "つき"}
]

# Conectar a la base de datos
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar si hay datos en la tabla
cursor.execute("SELECT COUNT(*) FROM kanji")
count = cursor.fetchone()[0]

if count == 0:
    try:
        # Usar directamente los datos básicos predefinidos
        kanji_data = basic_kanji_data
        print(f"Usando {len(kanji_data)} kanji básicos predefinidos")
        
        # Insertar datos en la tabla
        for item in kanji_data:
            cursor.execute(
                "INSERT INTO kanji (kanji, significado, lectura_china, lectura_japonesa) VALUES (?, ?, ?, ?)",
                (item["kanji"], item["significado"], item["lectura_china"], item["lectura_japonesa"])
            )
        
        conn.commit()
        print(f"Se insertaron {len(kanji_data)} registros en la tabla 'kanji'")
    except Exception as e:
        print(f"Error al insertar datos: {e}")
else:
    print(f"La tabla 'kanji' ya contiene {count} registros. No se insertaron nuevos datos.")

# Mostrar las 10 primeras filas de la tabla kanji
print("\n=== 10 PRIMERAS FILAS DE LA TABLA KANJI ===")
cursor.execute("SELECT * FROM kanji LIMIT 10")
for row in cursor.fetchall():
    print(row)

# Mostrar las 10 primeras filas de la tabla palabras_frecuentes
print("\n=== 10 PRIMERAS FILAS DE LA TABLA PALABRAS_FRECUENTES ===")
cursor.execute("SELECT * FROM palabras_frecuentes LIMIT 10")
for row in cursor.fetchall():
    print(row)

# Cerrar la conexión
conn.close() 