from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pathlib import Path

from . import config_routes
from . import quiz_routes
from ..config.srs_config import config as srs_config

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
KANJI_DB_PATH = DATA_DIR / 'kanji.db'

app = FastAPI(title="Kanji Quiz API")

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(config_routes.router)
app.include_router(quiz_routes.router)

def init_db():
    """Inicializa la base de datos si no existe"""
    conn = sqlite3.connect(KANJI_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kanji (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kanji TEXT UNIQUE NOT NULL,
        significado TEXT,
        lectura_china TEXT,
        lectura_japonesa TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 