from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import sqlite3
import os
import logging
import random

from src.processing.srs_utils import (
    load_cards, load_state, save_state, sm2_update,
    choose_due, get_distractors
)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kanji SRS API",
    description="API para el sistema de repaso espaciado de kanjis",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class Card(BaseModel):
    kanji: str
    meaning: str

class CardState(BaseModel):
    kanji: str
    due: datetime
    interval: float
    ease_factor: float
    repetitions: int

class QuizResponse(BaseModel):
    card: Card
    choices: List[str]
    is_review: bool = False

class AnswerRequest(BaseModel):
    kanji: str
    selected_choice: str

class AnswerResponse(BaseModel):
    correct: bool
    correct_answer: str
    next_due: datetime

# Conexión a la base de datos
def get_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'kanji_data.db')
    if not os.path.exists(db_path):
        logger.error(f"La base de datos {db_path} no existe")
        raise HTTPException(status_code=500, detail="La base de datos no existe. Por favor, ejecuta primero init_db.py")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error al conectar a la base de datos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al conectar a la base de datos: {str(e)}")

def load_cards() -> List[Card]:
    """Carga todas las tarjetas desde la base de datos."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT char as kanji, meaning
    FROM characters
    ''')
    
    cards = [Card(**dict(row)) for row in cursor.fetchall()]
    conn.close()
    return cards

def load_state() -> dict:
    """Carga el estado SRS desde la base de datos."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT char, next_review, ease_factor, interval, repetitions
    FROM srs_progress
    ''')
    
    state = {}
    for row in cursor.fetchall():
        state[row['char']] = {
            'due': datetime.fromisoformat(row['next_review']) if row['next_review'] else datetime.now(),
            'interval': row['interval'],
            'ease_factor': row['ease_factor'],
            'repetitions': row['repetitions']
        }
    
    conn.close()
    return state

def save_state(state: dict) -> None:
    """Guarda el estado SRS en la base de datos."""
    conn = get_db()
    cursor = conn.cursor()
    
    for kanji, card_state in state.items():
        cursor.execute('''
        UPDATE srs_progress
        SET next_review = ?, ease_factor = ?, interval = ?, repetitions = ?
        WHERE char = ?
        ''', (
            card_state['due'].isoformat(),
            card_state['ease_factor'],
            card_state['interval'],
            card_state['repetitions'],
            kanji
        ))
    
    conn.commit()
    conn.close()

def sm2_update(card_state: dict, quality: int) -> dict:
    """Actualiza el estado de una tarjeta usando el algoritmo SM-2."""
    if quality < 3:  # Respuesta incorrecta o difícil
        card_state['repetitions'] = 0
        card_state['interval'] = 0
    else:  # Respuesta correcta
        card_state['repetitions'] += 1
        if card_state['repetitions'] == 1:
            card_state['interval'] = 1
        elif card_state['repetitions'] == 2:
            card_state['interval'] = 6
        else:
            card_state['interval'] = int(card_state['interval'] * card_state['ease_factor'])
    
    # Ajustar ease factor
    card_state['ease_factor'] = max(1.3, card_state['ease_factor'] + 
        (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    
    # Calcular siguiente revisión
    if quality < 3:
        card_state['due'] = datetime.now() + timedelta(minutes=10)
    else:
        card_state['due'] = datetime.now() + timedelta(days=card_state['interval'])
    
    return card_state

def choose_due(cards: List[Card], state: dict) -> List[Card]:
    """Selecciona las tarjetas que están pendientes de repaso."""
    now = datetime.now()
    return [card for card in cards if state[card.kanji]['due'] <= now]

def get_distractors(cards: List[Card], correct: str, 
                   getter: callable, n: int = 3) -> List[str]:
    """Obtiene distractores aleatorios para una tarjeta."""
    all_values = [getter(card) for card in cards if getter(card) != correct]
    return random.sample(all_values, min(n, len(all_values)))

@app.get("/")
async def root():
    return {"message": "Kanji SRS API"}

@app.get("/cards", response_model=List[Card])
async def get_cards():
    """Obtiene todas las tarjetas disponibles."""
    try:
        return load_cards()
    except Exception as e:
        logger.error(f"Error al cargar tarjetas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cards/due", response_model=List[Card])
async def get_due_cards():
    """Obtiene las tarjetas que están pendientes de repaso."""
    try:
        cards = load_cards()
        state = load_state()
        return choose_due(cards, state)
    except Exception as e:
        logger.error(f"Error al obtener tarjetas pendientes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz/kanji-to-meaning", response_model=QuizResponse)
async def get_kanji_quiz():
    """Obtiene una pregunta de kanji a significado."""
    try:
        cards = load_cards()
        state = load_state()
        due = choose_due(cards, state)
        
        if not due:
            raise HTTPException(status_code=404, detail="No hay tarjetas pendientes")
        
        card = due[0]  # Tomamos la primera tarjeta pendiente
        distractors = get_distractors(cards, card.meaning, lambda c: c.meaning)
        choices = distractors + [card.meaning]
        
        return QuizResponse(
            card=card,
            choices=choices,
            is_review=False
        )
    except Exception as e:
        logger.error(f"Error al obtener quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/quiz/meaning-to-kanji", response_model=QuizResponse)
async def get_meaning_quiz():
    """Obtiene una pregunta de significado a kanji."""
    try:
        cards = load_cards()
        state = load_state()
        due = choose_due(cards, state)
        
        if not due:
            raise HTTPException(status_code=404, detail="No hay tarjetas pendientes")
        
        card = due[0]  # Tomamos la primera tarjeta pendiente
        distractors = get_distractors(cards, card.kanji, lambda c: c.kanji)
        choices = distractors + [card.kanji]
        
        return QuizResponse(
            card=card,
            choices=choices,
            is_review=False
        )
    except Exception as e:
        logger.error(f"Error al obtener quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/answer", response_model=AnswerResponse)
async def submit_answer(request: AnswerRequest):
    """Procesa una respuesta y actualiza el estado de la tarjeta."""
    try:
        cards = load_cards()
        state = load_state()
        
        # Encontrar la tarjeta correspondiente
        card = next((c for c in cards if c.kanji == request.kanji), None)
        if not card:
            raise HTTPException(status_code=404, detail="Tarjeta no encontrada")
        
        # Verificar la respuesta
        correct = request.selected_choice == card.meaning
        
        # Actualizar el estado
        quality = 5 if correct else 2
        state[request.kanji] = sm2_update(state[request.kanji], quality)
        save_state(state)
        
        return AnswerResponse(
            correct=correct,
            correct_answer=card.meaning,
            next_due=state[request.kanji]['due']
        )
    except Exception as e:
        logger.error(f"Error al procesar respuesta: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    try:
        uvicorn.run(
            app, 
            host="127.0.0.1",  # Cambiado de 0.0.0.0 a 127.0.0.1 para mayor seguridad
            port=8001,  # Cambiado de 8000 a 8001
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error al iniciar el servidor: {str(e)}")
        print(f"Error al iniciar el servidor: {str(e)}")
        print("Intenta con un puerto diferente o asegúrate de que no hay otro proceso usando el puerto.") 