import sqlite3
import os
import datetime
from typing import List, Dict, Any, Callable
import random

# --- CONFIG ---
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
CARDS_JSON = os.path.join(DATA_DIR, "kanji_meanings_readings.json")
STATE_JSON = os.path.join(DATA_DIR, "srs_state.json")
NUM_CHOICES = 5

# SM-2 parameters
MIN_EASINESS = 1.3
DEFAULT_EASINESS = 2.5

def get_db():
    """Obtiene una conexión a la base de datos."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'kanji_data.db')
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"La base de datos {db_path} no existe")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def load_cards() -> List[Dict[str, Any]]:
    """Carga todas las tarjetas desde la base de datos."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT c.char as kanji, c.meaning
    FROM characters c
    ''')
    
    cards = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return cards

def load_state(cards: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Carga el estado SRS de las tarjetas desde la base de datos."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT char, next_review, ease_factor, interval, repetitions
    FROM srs_progress
    ''')
    
    state = {}
    for row in cursor.fetchall():
        state[row['char']] = {
            'due': datetime.datetime.fromisoformat(row['next_review']) if row['next_review'] else datetime.datetime.now(),
            'interval': row['interval'],
            'ease_factor': row['ease_factor'],
            'repetitions': row['repetitions']
        }
    
    # Asegurar que todas las tarjetas tienen estado
    for card in cards:
        if card['kanji'] not in state:
            state[card['kanji']] = {
                'due': datetime.datetime.now(),
                'interval': 0,
                'ease_factor': 2.5,
                'repetitions': 0
            }
    
    conn.close()
    return state

def save_state(state: Dict[str, Dict[str, Any]]) -> None:
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

def sm2_update(card_state: Dict[str, Any], quality: int) -> Dict[str, Any]:
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
        card_state['due'] = datetime.datetime.now() + datetime.timedelta(minutes=10)
    else:
        card_state['due'] = datetime.datetime.now() + datetime.timedelta(days=card_state['interval'])
    
    return card_state

def choose_due(cards: List[Dict[str, Any]], state: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Selecciona las tarjetas que están pendientes de repaso."""
    now = datetime.datetime.now()
    return [card for card in cards if state[card['kanji']]['due'] <= now]

def get_distractors(cards: List[Dict[str, Any]], correct: str, 
                   getter: Callable[[Dict[str, Any]], str], 
                   n: int = 3) -> List[str]:
    """Obtiene distractores aleatorios para una tarjeta."""
    all_values = [getter(card) for card in cards if getter(card) != correct]
    return random.sample(all_values, min(n, len(all_values))) 