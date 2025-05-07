from pathlib import Path

# Obtener la ruta base del proyecto (donde está la carpeta src)
BASE_DIR = Path(__file__).parent.parent.parent

# Rutas de datos
DATA_DIR = BASE_DIR / 'data'
KANJI_DB_PATH = DATA_DIR / 'kanji.db'
KANJI_JSON_PATH = DATA_DIR / 'kanji_data.json'

# Crear directorio de datos si no existe
DATA_DIR.mkdir(exist_ok=True) 