from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import sqlite3
from pathlib import Path
import json
import datetime
import random
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

# Configuración de rutas
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
KANJI_DB_PATH = DATA_DIR / 'kanji.db'
STATE_JSON = DATA_DIR / 'srs_state_significado_kanji.json'
DATA_DIR.mkdir(exist_ok=True)

# Configuración SRS
NUM_CHOICES = 5
MIN_EASINESS = 1.3
DEFAULT_EASINESS = 2.5

app = FastAPI(title="Kanji Quiz API")

# Configuración más específica de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.middleware("http")
async def add_cors_headers(request, call_next):
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "3600"
        return response
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# Modelos Pydantic
class KanjiCard(BaseModel):
    kanji: str
    significado: str
    lectura_china: Optional[str] = None
    lectura_japonesa: Optional[str] = None

class QuizQuestion(BaseModel):
    kanji: str
    options: List[str]
    correct_option: int

class QuizResponse(BaseModel):
    correct: bool
    correct_answer: str
    next_due: str

class SignificadoKanjiQuestion(BaseModel):
    significado: str
    options: List[str]
    correct_option: int

class LecturaKanjiQuestion(BaseModel):
    kanji: str
    options: List[str]
    correct_option: int
    reading_type: str  # "china" o "japonesa"

class LecturaToKanjiQuestion(BaseModel):
    lectura: str
    reading_type: str  # "china" o "japonesa"
    options: List[str]
    correct_option: int

class KanjiAnswer(BaseModel):
    kanji: str
    answer: int

class SignificadoAnswer(BaseModel):
    significado: str
    answer: int

class LecturaKanjiAnswer(BaseModel):
    kanji: str
    reading_type: str
    answer: int

class LecturaToKanjiAnswer(BaseModel):
    lectura: str
    reading_type: str
    answer: int

class QuizState(BaseModel):
    question_id: str
    correct_option: int

# Variable global para almacenar el estado de las preguntas actuales
current_quiz_states: Dict[str, QuizState] = {}

# Funciones de base de datos
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
    
    cursor.execute("SELECT kanji, significado, lectura_china, lectura_japonesa FROM kanji")
    cards = [
        {
            "kanji": row[0],
            "significado": row[1],
            "lectura_china": row[2],
            "lectura_japonesa": row[3]
        } for row in cursor.fetchall()
    ]
    conn.close()
    
    return cards

def load_state(cards):
    """Carga o inicializa el estado SRS"""
    if STATE_JSON.exists():
        with open(STATE_JSON, encoding="utf-8") as f:
            return json.load(f)
    
    today = datetime.date.today().isoformat()
    state = {}
    
    # Inicializar estado para cada kanji y sus lecturas
    for card in cards:
        # Estado básico del kanji
        state[card["kanji"]] = {
            "interval": 0,
            "repetitions": 0,
            "easiness": DEFAULT_EASINESS,
            "due": today
        }
        
        # Estado para lectura china
        if card["lectura_china"]:
            state[f"{card['kanji']}_china"] = {
                "interval": 0,
                "repetitions": 0,
                "easiness": DEFAULT_EASINESS,
                "due": today
            }
        
        # Estado para lectura japonesa
        if card["lectura_japonesa"]:
            state[f"{card['kanji']}_japonesa"] = {
                "interval": 0,
                "repetitions": 0,
                "easiness": DEFAULT_EASINESS,
                "due": today
            }
    
    return state

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
    return [card for card in cards if state[card["kanji"]]["due"] <= today]

def generate_choices(cards, correct_meaning):
    """Genera opciones múltiples para el quiz"""
    all_meanings = [card["significado"] for card in cards if card["significado"] != correct_meaning]
    
    # Seleccionar significados aleatorios
    choices = random.sample(all_meanings, min(NUM_CHOICES - 1, len(all_meanings)))
    choices.append(correct_meaning)
    random.shuffle(choices)
    
    return choices

def generate_kanji_choices(cards, correct_kanji):
    """Genera opciones múltiples de kanji para el quiz"""
    all_kanji = [card["kanji"] for card in cards if card["kanji"] != correct_kanji]
    
    # Seleccionar kanji aleatorios
    choices = random.sample(all_kanji, min(NUM_CHOICES - 1, len(all_kanji)))
    choices.append(correct_kanji)
    random.shuffle(choices)
    
    return choices

def generate_reading_choices(cards, correct_reading):
    """Genera opciones múltiples de lecturas para el quiz"""
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

# Endpoints
@app.get("/")
async def root():
    return {"message": "Kanji Quiz API"}

@app.get("/quiz/kanji-significado", response_model=QuizQuestion)
async def get_kanji_significado_question():
    """Obtiene una pregunta para el quiz de kanji a significado"""
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    state = load_state(cards)
    due_cards = choose_due_cards(cards, state)
    
    if not due_cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas pendientes para hoy")
    
    # Seleccionar una tarjeta aleatoria
    card = random.choice(due_cards)
    
    # Generar opciones
    choices = generate_choices(cards, card["significado"])
    
    # Encontrar el índice de la respuesta correcta
    correct_option = choices.index(card["significado"]) + 1
    
    # Guardar el estado de la pregunta
    question_id = f"kanji_significado_{card['kanji']}"
    current_quiz_states[question_id] = QuizState(
        question_id=question_id,
        correct_option=correct_option
    )
    
    return {
        "kanji": card["kanji"],
        "options": choices,
        "correct_option": correct_option
    }

@app.post("/quiz/kanji-significado/answer", response_model=QuizResponse)
async def answer_kanji_significado(answer_data: KanjiAnswer):
    """Procesa la respuesta del quiz de kanji a significado"""
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    state = load_state(cards)
    
    # Encontrar la tarjeta
    card = next((c for c in cards if c["kanji"] == answer_data.kanji), None)
    if not card:
        raise HTTPException(status_code=404, detail="Kanji no encontrado")
    
    # Obtener el estado de la pregunta
    question_id = f"kanji_significado_{answer_data.kanji}"
    quiz_state = current_quiz_states.get(question_id)
    if not quiz_state:
        raise HTTPException(status_code=400, detail="Pregunta no válida o expirada")
    
    # Verificar respuesta
    correct = answer_data.answer == quiz_state.correct_option
    quality = 5 if correct else 1
    
    # Actualizar estado SRS
    state[answer_data.kanji] = sm2_update(state[answer_data.kanji], quality)
    save_state(state)
    
    # Limpiar el estado de la pregunta
    current_quiz_states.pop(question_id, None)
    
    return {
        "correct": correct,
        "correct_answer": card["significado"],
        "next_due": state[answer_data.kanji]["due"]
    }

@app.get("/quiz/significado-kanji", response_model=SignificadoKanjiQuestion)
async def get_significado_kanji_question():
    """Obtiene una pregunta para el quiz de significado a kanji"""
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    state = load_state(cards)
    due_cards = choose_due_cards(cards, state)
    
    if not due_cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas pendientes para hoy")
    
    # Seleccionar una tarjeta aleatoria
    card = random.choice(due_cards)
    
    # Generar opciones de kanji
    choices = generate_kanji_choices(cards, card["kanji"])
    
    # Encontrar el índice de la respuesta correcta
    correct_option = choices.index(card["kanji"]) + 1
    
    # Guardar el estado de la pregunta
    question_id = f"significado_kanji_{card['significado']}"
    current_quiz_states[question_id] = QuizState(
        question_id=question_id,
        correct_option=correct_option
    )
    
    return {
        "significado": card["significado"],
        "options": choices,
        "correct_option": correct_option
    }

@app.post("/quiz/significado-kanji/answer", response_model=QuizResponse)
async def answer_significado_kanji(answer_data: SignificadoAnswer):
    """Procesa la respuesta del quiz de significado a kanji"""
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    state = load_state(cards)
    
    # Encontrar la tarjeta
    card = next((c for c in cards if c["significado"] == answer_data.significado), None)
    if not card:
        raise HTTPException(status_code=404, detail="Significado no encontrado")
    
    # Obtener el estado de la pregunta
    question_id = f"significado_kanji_{answer_data.significado}"
    quiz_state = current_quiz_states.get(question_id)
    if not quiz_state:
        raise HTTPException(status_code=400, detail="Pregunta no válida o expirada")
    
    # Verificar respuesta
    correct = answer_data.answer == quiz_state.correct_option
    quality = 5 if correct else 1
    
    # Actualizar estado SRS
    state[card["kanji"]] = sm2_update(state[card["kanji"]], quality)
    save_state(state)
    
    return {
        "correct": correct,
        "correct_answer": card["kanji"],
        "next_due": state[card["kanji"]]["due"]
    }

@app.get("/quiz/kanji-lectura", response_model=LecturaKanjiQuestion)
async def get_lectura_kanji_question():
    """Obtiene una pregunta para el quiz de lectura de kanji"""
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    state = load_state(cards)
    due_cards = choose_due_cards(cards, state)
    
    if not due_cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas pendientes para hoy")
    
    # Seleccionar una tarjeta aleatoria
    card = random.choice(due_cards)
    
    # Determinar si preguntar por lectura china o japonesa
    reading_type = random.choice(["china", "japonesa"])
    correct_reading = card["lectura_china"] if reading_type == "china" else card["lectura_japonesa"]
    
    if not correct_reading:
        # Si no hay lectura del tipo seleccionado, intentar con el otro tipo
        reading_type = "japonesa" if reading_type == "china" else "china"
        correct_reading = card["lectura_china"] if reading_type == "china" else card["lectura_japonesa"]
        
        if not correct_reading:
            raise HTTPException(status_code=404, detail="No hay lecturas disponibles para este kanji")
    
    # Generar opciones
    choices = generate_reading_choices(cards, correct_reading)
    
    # Encontrar el índice de la respuesta correcta
    correct_option = choices.index(correct_reading) + 1
    
    # Guardar el estado de la pregunta
    question_id = f"kanji_lectura_{card['kanji']}_{reading_type}"
    current_quiz_states[question_id] = QuizState(
        question_id=question_id,
        correct_option=correct_option
    )
    
    return {
        "kanji": card["kanji"],
        "options": choices,
        "correct_option": correct_option,
        "reading_type": reading_type
    }

@app.post("/quiz/kanji-lectura/answer", response_model=QuizResponse)
async def answer_lectura_kanji(answer_data: LecturaKanjiAnswer):
    """Procesa la respuesta del quiz de lectura de kanji"""
    print(f"Recibiendo respuesta para kanji-lectura: {answer_data}")
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    state = load_state(cards)
    
    # Encontrar la tarjeta
    card = next((c for c in cards if c["kanji"] == answer_data.kanji), None)
    if not card:
        raise HTTPException(status_code=404, detail="Kanji no encontrado")
    
    # Obtener la lectura correcta
    correct_reading = card["lectura_china"] if answer_data.reading_type == "china" else card["lectura_japonesa"]
    if not correct_reading:
        raise HTTPException(status_code=404, detail="Tipo de lectura no disponible para este kanji")
    
    print(f"Lectura correcta: {correct_reading}")
    
    # Obtener el estado de la pregunta
    question_id = f"kanji_lectura_{answer_data.kanji}_{answer_data.reading_type}"
    quiz_state = current_quiz_states.get(question_id)
    if not quiz_state:
        raise HTTPException(status_code=400, detail="Pregunta no válida o expirada")
    
    # Verificar respuesta
    correct = answer_data.answer == quiz_state.correct_option
    quality = 5 if correct else 1
    
    # Actualizar estado SRS
    state_key = f"{answer_data.kanji}_{answer_data.reading_type}"
    state[state_key] = sm2_update(state[state_key], quality)
    save_state(state)
    
    # Limpiar el estado de la pregunta
    current_quiz_states.pop(question_id, None)
    
    return {
        "correct": correct,
        "correct_answer": correct_reading,
        "next_due": state[state_key]["due"]
    }

@app.get("/quiz/lectura-kanji", response_model=LecturaToKanjiQuestion)
async def get_lectura_to_kanji_question():
    """Obtiene una pregunta para el quiz de lectura a kanji"""
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    state = load_state(cards)
    due_cards = choose_due_cards(cards, state)
    
    if not due_cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas pendientes para hoy")
    
    # Seleccionar una tarjeta aleatoria y tipo de lectura
    card = random.choice(due_cards)
    reading_type = random.choice(["china", "japonesa"])
    correct_reading = card["lectura_china"] if reading_type == "china" else card["lectura_japonesa"]
    
    if not correct_reading:
        reading_type = "japonesa" if reading_type == "china" else "china"
        correct_reading = card["lectura_china"] if reading_type == "china" else card["lectura_japonesa"]
        if not correct_reading:
            raise HTTPException(status_code=404, detail="No hay lecturas disponibles para este kanji")
    
    # Generar opciones de kanji
    all_kanji = [c["kanji"] for c in cards if (
        (reading_type == "china" and c["lectura_china"] != correct_reading) or
        (reading_type == "japonesa" and c["lectura_japonesa"] != correct_reading)
    )]
    
    choices = random.sample(all_kanji, min(NUM_CHOICES - 1, len(all_kanji)))
    choices.append(card["kanji"])
    random.shuffle(choices)
    
    correct_option = choices.index(card["kanji"]) + 1
    
    # Guardar el estado de la pregunta
    question_id = f"lectura_kanji_{correct_reading}_{reading_type}"
    current_quiz_states[question_id] = QuizState(
        question_id=question_id,
        correct_option=correct_option
    )
    
    return {
        "lectura": correct_reading,
        "reading_type": reading_type,
        "options": choices,
        "correct_option": correct_option
    }

@app.post("/quiz/lectura-kanji/answer", response_model=QuizResponse)
async def answer_lectura_to_kanji(answer_data: LecturaToKanjiAnswer):
    """Procesa la respuesta del quiz de lectura a kanji"""
    print(f"Recibiendo respuesta para lectura-kanji: {answer_data}")
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    state = load_state(cards)
    
    # Encontrar la tarjeta
    card = next((c for c in cards if (
        (answer_data.reading_type == "china" and c["lectura_china"] == answer_data.lectura) or
        (answer_data.reading_type == "japonesa" and c["lectura_japonesa"] == answer_data.lectura)
    )), None)
    
    if not card:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    
    print(f"Kanji encontrado: {card['kanji']}")
    
    # Obtener el estado de la pregunta
    question_id = f"lectura_kanji_{answer_data.lectura}_{answer_data.reading_type}"
    quiz_state = current_quiz_states.get(question_id)
    if not quiz_state:
        raise HTTPException(status_code=400, detail="Pregunta no válida o expirada")
    
    # Verificar respuesta y actualizar SRS
    correct = answer_data.answer == quiz_state.correct_option
    quality = 5 if correct else 1
    state_key = f"{card['kanji']}_{answer_data.reading_type}"
    state[state_key] = sm2_update(state[state_key], quality)
    save_state(state)
    
    # Limpiar el estado de la pregunta
    current_quiz_states.pop(question_id, None)
    
    return {
        "correct": correct,
        "correct_answer": card["kanji"],
        "next_due": state[state_key]["due"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 