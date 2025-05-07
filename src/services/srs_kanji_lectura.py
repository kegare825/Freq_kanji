import json
import random
import datetime
import os
import sqlite3
import sys
from pathlib import Path

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.utils.config import DB_PATH, SRS_STATE_LECTURA_PATH

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
KANJI_DB_PATH = DATA_DIR / 'kanji.db'
STATE_JSON = DATA_DIR / 'srs_state_kanji_lectura.json'
DATA_DIR.mkdir(exist_ok=True)

# --- CONFIG ---
NUM_CHOICES = 5

# SM-2 parameters
MIN_EASINESS = 1.3
DEFAULT_EASINESS = 2.5

# --- HELPERS ---
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

def load_cards():
    """Carga las tarjetas desde la base de datos"""
    init_db()
    
    conn = sqlite3.connect(KANJI_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT kanji, lectura_china, lectura_japonesa FROM kanji")
    cards = [{"kanji": row[0], "lectura_china": row[1], "lectura_japonesa": row[2]} for row in cursor.fetchall()]
    conn.close()
    
    return cards

def load_state(cards):
    """Carga o inicializa el estado SRS"""
    if STATE_JSON.exists():
        with open(STATE_JSON, encoding="utf-8") as f:
            return json.load(f)
    
    today = datetime.date.today().isoformat()
    return {
        f"{card['kanji']}_china": {
            "interval": 0,
            "repetitions": 0,
            "easiness": DEFAULT_EASINESS,
            "due": today
        } for card in cards
    } | {
        f"{card['kanji']}_japonesa": {
            "interval": 0,
            "repetitions": 0,
            "easiness": DEFAULT_EASINESS,
            "due": today
        } for card in cards
    }

def save_state(state):
    """Guarda el estado SRS"""
    with open(STATE_JSON, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def sm2_update(card_state, quality):
    """Actualiza el estado de la tarjeta usando el algoritmo SM-2"""
    if quality < 3:
        card_state["repetitions"] = 0
        card_state["interval"] = 0
    else:
        if card_state["repetitions"] == 0:
            card_state["interval"] = 1
        elif card_state["repetitions"] == 1:
            card_state["interval"] = 6
        else:
            card_state["interval"] = round(card_state["interval"] * card_state["easiness"])
        card_state["repetitions"] += 1

    ef = card_state["easiness"] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    card_state["easiness"] = max(MIN_EASINESS, ef)

    next_due = datetime.date.today() + datetime.timedelta(days=card_state["interval"])
    card_state["due"] = next_due.isoformat()
    return card_state

def choose_due_cards(cards, state):
    """Selecciona las tarjetas que están pendientes para hoy"""
    today = datetime.date.today().isoformat()
    due = []
    for card in cards:
        if state[f"{card['kanji']}_china"]["due"] <= today:
            due.append((card, "china"))
        if state[f"{card['kanji']}_japonesa"]["due"] <= today:
            due.append((card, "japonesa"))
    return due

def generate_choices(cards, correct_reading):
    """Genera opciones múltiples para el quiz"""
    all_readings = []
    for card in cards:
        if card["lectura_china"]:
            all_readings.append(card["lectura_china"])
        if card["lectura_japonesa"]:
            all_readings.append(card["lectura_japonesa"])
    
    # Filtrar lecturas únicas y eliminar la correcta
    unique_readings = list(set(all_readings))
    if correct_reading in unique_readings:
        unique_readings.remove(correct_reading)
    
    # Seleccionar lecturas aleatorias
    choices = random.sample(unique_readings, min(NUM_CHOICES - 1, len(unique_readings)))
    choices.append(correct_reading)
    random.shuffle(choices)
    
    return choices

# --- QUIZ LOOP ---
def quiz():
    """Inicia el quiz de kanji"""
    cards = load_cards()
    if not cards:
        print("No hay tarjetas disponibles. Asegúrate de que la base de datos contiene datos.")
        return
    
    state = load_state(cards)
    
    while True:
        due_cards = choose_due_cards(cards, state)
        if not due_cards:
            print("\n¡No hay más tarjetas pendientes para hoy!")
            break
        
        # Seleccionar una tarjeta aleatoria de las pendientes
        card, reading_type = random.choice(due_cards)
        
        # Determinar la lectura correcta
        correct_reading = card["lectura_china"] if reading_type == "china" else card["lectura_japonesa"]
        if not correct_reading:
            continue
        
        # Generar opciones
        choices = generate_choices(cards, correct_reading)
        
        print(f"\nKanji: {card['kanji']}")
        print("\nOpciones:")
        for i, choice in enumerate(choices, 1):
            print(f"{i}. {choice}")
        
        while True:
            try:
                respuesta = int(input("\nElige el número de la lectura correcta (1-5): "))
                if 1 <= respuesta <= len(choices):
                    break
                print("Por favor, elige un número válido.")
            except ValueError:
                print("Por favor, ingresa un número.")
        
        # Calcular calidad de respuesta (1-5)
        if choices[respuesta - 1] == correct_reading:
            print("\n¡Correcto!")
            quality = 5
        else:
            print(f"\nIncorrecto. La respuesta correcta era: {correct_reading}")
            quality = 1
        
        # Actualizar estado SRS
        state[f"{card['kanji']}_{reading_type}"] = sm2_update(state[f"{card['kanji']}_{reading_type}"], quality)
        save_state(state)
        
        # Mostrar progreso
        print(f"\nTarjetas restantes para hoy: {len(due_cards) - 1}")

if __name__ == "__main__":
    quiz() 