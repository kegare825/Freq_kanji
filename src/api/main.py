from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import datetime
from typing import List, Optional
import random
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="SRS Kanji", description="Sistema de repetición espaciada para kanji")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class KanjiReview(BaseModel):
    char: str
    rating: int  # 1-5, donde 1 es "No lo recuerdo" y 5 es "Muy fácil"

class KanjiCard(BaseModel):
    char: str
    aozora_freq: float
    news_freq: float
    wiki_freq: float
    next_review: Optional[datetime.datetime]
    ease_factor: float = 2.5
    interval: int = 0
    repetitions: int = 0

# Conexión a la base de datos
def get_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'kanji_data.db')
    if not os.path.exists(db_path):
        logger.error(f"La base de datos {db_path} no existe")
        raise HTTPException(status_code=500, detail="La base de datos no existe. Por favor, ejecuta primero import_to_db.py")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error al conectar a la base de datos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al conectar a la base de datos: {str(e)}")

# Inicializar la base de datos SRS
def init_srs_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Verificar si la tabla characters existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='characters'")
        if not cursor.fetchone():
            logger.error("La tabla 'characters' no existe en la base de datos")
            raise HTTPException(status_code=500, detail="La tabla 'characters' no existe en la base de datos")
        
        # Crear tabla para el seguimiento SRS
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS srs_progress (
            char TEXT PRIMARY KEY,
            next_review DATETIME,
            ease_factor REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 0,
            repetitions INTEGER DEFAULT 0,
            FOREIGN KEY (char) REFERENCES characters(char)
        )
        ''')
        
        # Insertar kanjis que no estén en la tabla srs_progress
        cursor.execute('''
        INSERT OR IGNORE INTO srs_progress (char)
        SELECT char FROM characters
        ''')
        
        # Verificar que se insertaron datos
        cursor.execute("SELECT COUNT(*) as count FROM srs_progress")
        count = cursor.fetchone()['count']
        logger.info(f"Se inicializaron {count} kanjis en srs_progress")
        
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Error al inicializar la base de datos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al inicializar la base de datos: {str(e)}")

# Algoritmo SRS (basado en SuperMemo 2)
def calculate_next_review(card: KanjiCard, rating: int) -> KanjiCard:
    if rating < 3:  # Respuesta incorrecta o difícil
        card.repetitions = 0
        card.interval = 0
    else:  # Respuesta correcta
        card.repetitions += 1
        if card.repetitions == 1:
            card.interval = 1
        elif card.repetitions == 2:
            card.interval = 6
        else:
            card.interval = int(card.interval * card.ease_factor)
    
    # Ajustar ease factor
    card.ease_factor = max(1.3, card.ease_factor + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02)))
    
    # Calcular siguiente revisión
    if rating < 3:
        card.next_review = datetime.datetime.now() + datetime.timedelta(minutes=10)
    else:
        card.next_review = datetime.datetime.now() + datetime.timedelta(days=card.interval)
    
    return card

@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando la aplicación...")
    init_srs_db()
    logger.info("Aplicación iniciada correctamente")

@app.get("/")
async def root():
    return {
        "message": "Bienvenido al SRS de Kanji",
        "endpoints": {
            "review": "/kanji/review",
            "stats": "/kanji/stats",
            "docs": "/docs"
        }
    }

@app.get("/kanji/review", response_model=List[KanjiCard])
async def get_kanji_to_review(limit: int = 10):
    try:
        logger.info(f"Obteniendo {limit} kanjis para revisar")
        conn = get_db()
        cursor = conn.cursor()
        
        # Obtener kanjis para revisar (los que están listos o nunca han sido revisados)
        cursor.execute('''
        SELECT c.char, c.aozora_char_freq, c.news_char_freq, c.wiki_char_freq,
               s.next_review, s.ease_factor, s.interval, s.repetitions
        FROM characters c
        JOIN srs_progress s ON c.char = s.char
        WHERE s.next_review <= datetime('now') OR s.next_review IS NULL
        ORDER BY RANDOM()
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        logger.info(f"Se encontraron {len(rows)} kanjis para revisar")
        
        if not rows:
            logger.warning("No hay kanjis para revisar en este momento")
            raise HTTPException(status_code=404, detail="No hay kanjis para revisar en este momento")
        
        cards = []
        for row in rows:
            try:
                card = KanjiCard(**dict(row))
                cards.append(card)
            except Exception as e:
                logger.error(f"Error al procesar fila: {row}, error: {str(e)}")
                continue
        
        conn.close()
        return cards
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@app.post("/kanji/review/{char}")
async def review_kanji(char: str, review: KanjiReview):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Obtener el estado actual del kanji
        cursor.execute('''
        SELECT * FROM srs_progress WHERE char = ?
        ''', (char,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Kanji no encontrado")
        
        card = KanjiCard(
            char=char,
            aozora_freq=0,
            news_freq=0,
            wiki_freq=0,
            next_review=row['next_review'],
            ease_factor=row['ease_factor'],
            interval=row['interval'],
            repetitions=row['repetitions']
        )
        
        # Calcular nuevo estado
        updated_card = calculate_next_review(card, review.rating)
        
        # Actualizar en la base de datos
        cursor.execute('''
        UPDATE srs_progress
        SET next_review = ?, ease_factor = ?, interval = ?, repetitions = ?
        WHERE char = ?
        ''', (
            updated_card.next_review,
            updated_card.ease_factor,
            updated_card.interval,
            updated_card.repetitions,
            char
        ))
        
        conn.commit()
        conn.close()
        
        return {"message": "Revisión registrada exitosamente"}
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

@app.get("/kanji/stats")
async def get_kanji_stats():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Obtener estadísticas generales
        cursor.execute('''
        SELECT 
            COUNT(*) as total_kanji,
            SUM(CASE WHEN next_review <= datetime('now') THEN 1 ELSE 0 END) as due_kanji,
            AVG(ease_factor) as avg_ease_factor
        FROM srs_progress
        ''')
        
        stats = dict(cursor.fetchone())
        conn.close()
        
        return stats
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001) 