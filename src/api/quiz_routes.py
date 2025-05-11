from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import random
from src.services.srs_service import SRSService
from src.config.srs_config import config as srs_config
from pathlib import Path
import sqlite3

router = APIRouter(prefix="/quiz", tags=["quiz"])

# Initialize SRS services
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
KANJI_DB_PATH = DATA_DIR / 'kanji.db'
significado_srs = SRSService(DATA_DIR / 'srs_state_significado_kanji.json')
lectura_srs = SRSService(DATA_DIR / 'srs_state_lectura_kanji.json')

# Cache for storing correct answers
answer_cache: Dict[str, int] = {}

# Models
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

class KanjiAnswer(BaseModel):
    kanji: str
    answer: int

class LecturaKanjiQuestion(BaseModel):
    kanji: str
    options: List[str]
    correct_option: int
    reading_type: str

class LecturaKanjiAnswer(BaseModel):
    kanji: Optional[str] = None
    lectura: Optional[str] = None
    reading_type: str
    answer: int

    @property
    def reading_value(self) -> str:
        """Returns either kanji or lectura value"""
        return self.kanji or self.lectura or ""

class SignificadoKanjiQuestion(BaseModel):
    significado: str
    options: List[str]
    correct_option: int

class SignificadoKanjiAnswer(BaseModel):
    significado: str
    answer: int

def generate_choices(cards: List[Dict], target: str, field: str = "significado") -> List[str]:
    """Generate quiz options"""
    all_options = [card[field] for card in cards if card[field]]
    unique_options = list(set(all_options) - {target})
    choices = random.sample(unique_options, min(srs_config.num_choices - 1, len(unique_options)))
    choices.append(target)
    random.shuffle(choices)
    return choices

def load_cards():
    """Carga las tarjetas desde la base de datos"""
    conn = sqlite3.connect(KANJI_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, kanji, significado, lectura_china, lectura_japonesa FROM kanji")
    cards = [
        {
            "id": row[0],
            "kanji": row[1],
            "significado": row[2],
            "lectura_china": row[3],
            "lectura_japonesa": row[4]
        } for row in cursor.fetchall()
    ]
    conn.close()
    
    return cards

@router.get("/kanji-significado", response_model=QuizQuestion)
async def get_kanji_significado_question():
    """Get a kanji to meaning quiz question"""
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    due_cards = significado_srs.get_due_cards(cards)
    if not due_cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas pendientes para hoy")
    
    card = random.choice(due_cards)
    choices = generate_choices(cards, card["significado"])
    correct_option = choices.index(card["significado"]) + 1
    
    # Cache the correct option for this kanji
    answer_cache[card["kanji"]] = correct_option
    
    return {
        "kanji": card["kanji"],
        "options": choices,
        "correct_option": correct_option
    }

@router.post("/kanji-significado/answer", response_model=QuizResponse)
async def answer_kanji_significado(answer: KanjiAnswer):
    """Process a kanji to meaning quiz answer"""
    cards = load_cards()
    card = next((c for c in cards if c["kanji"] == answer.kanji), None)
    if not card:
        raise HTTPException(status_code=404, detail="Kanji no encontrado")
    
    # Get the correct option from cache
    correct_option = answer_cache.get(answer.kanji)
    if correct_option is None:
        raise HTTPException(status_code=400, detail="Pregunta expirada o inválida")
    
    quality = 5 if answer.answer == correct_option else 1
    new_state = significado_srs.update_card(str(card["id"]), quality)
    
    # Clean up cache
    answer_cache.pop(answer.kanji, None)
    
    return {
        "correct": quality == 5,
        "correct_answer": card["significado"],
        "next_due": new_state["due"]
    }

@router.get("/kanji-lectura", response_model=LecturaKanjiQuestion)
async def get_kanji_lectura_question():
    """Get a kanji to reading quiz question"""
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    due_cards = lectura_srs.get_due_cards(cards)
    if not due_cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas pendientes para hoy")
    
    card = random.choice(due_cards)
    reading_type = random.choice(["china", "japonesa"])
    correct_reading = card["lectura_china"] if reading_type == "china" else card["lectura_japonesa"]
    
    if not correct_reading:
        reading_type = "japonesa" if reading_type == "china" else "china"
        correct_reading = card["lectura_china"] if reading_type == "china" else card["lectura_japonesa"]
        if not correct_reading:
            raise HTTPException(status_code=404, detail="No hay lecturas disponibles para este kanji")
    
    choices = generate_choices(cards, correct_reading, f"lectura_{reading_type}")
    correct_option = choices.index(correct_reading) + 1
    
    # Cache the correct option for this kanji and reading type
    answer_cache[f"{card['kanji']}_{reading_type}"] = correct_option
    
    return {
        "kanji": card["kanji"],
        "options": choices,
        "correct_option": correct_option,
        "reading_type": reading_type
    }

@router.post("/kanji-lectura/answer", response_model=QuizResponse)
async def answer_kanji_lectura(answer: LecturaKanjiAnswer):
    """Process a kanji to reading quiz answer"""
    cards = load_cards()
    card = next((c for c in cards if c["kanji"] == answer.kanji), None)
    if not card:
        raise HTTPException(status_code=404, detail="Kanji no encontrado")
    
    # Get the correct option from cache
    cache_key = f"{answer.kanji}_{answer.reading_type}"
    correct_option = answer_cache.get(cache_key)
    if correct_option is None:
        raise HTTPException(status_code=400, detail="Pregunta expirada o inválida")
    
    correct_reading = card["lectura_china"] if answer.reading_type == "china" else card["lectura_japonesa"]
    if not correct_reading:
        raise HTTPException(status_code=404, detail="Tipo de lectura no disponible para este kanji")
    
    quality = 5 if answer.answer == correct_option else 1
    new_state = lectura_srs.update_card(f"{card['id']}_{answer.reading_type}", quality)
    
    # Clean up cache
    answer_cache.pop(cache_key, None)
    
    return {
        "correct": quality == 5,
        "correct_answer": correct_reading,
        "next_due": new_state["due"]
    }

@router.get("/significado-kanji", response_model=SignificadoKanjiQuestion)
async def get_significado_kanji_question():
    """Get a meaning to kanji quiz question"""
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    due_cards = significado_srs.get_due_cards(cards)
    if not due_cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas pendientes para hoy")
    
    card = random.choice(due_cards)
    choices = generate_choices(cards, card["kanji"], "kanji")
    correct_option = choices.index(card["kanji"]) + 1
    
    # Cache the correct option for this significado
    answer_cache[card["significado"]] = correct_option
    
    return {
        "significado": card["significado"],
        "options": choices,
        "correct_option": correct_option
    }

@router.post("/significado-kanji/answer", response_model=QuizResponse)
async def answer_significado_kanji(answer: SignificadoKanjiAnswer):
    """Process a meaning to kanji quiz answer"""
    cards = load_cards()
    card = next((c for c in cards if c["significado"] == answer.significado), None)
    if not card:
        raise HTTPException(status_code=404, detail="Significado no encontrado")
    
    # Get the correct option from cache
    correct_option = answer_cache.get(answer.significado)
    if correct_option is None:
        raise HTTPException(status_code=400, detail="Pregunta expirada o inválida")
    
    quality = 5 if answer.answer == correct_option else 1
    new_state = significado_srs.update_card(str(card["id"]), quality)
    
    # Clean up cache
    answer_cache.pop(answer.significado, None)
    
    return {
        "correct": quality == 5,
        "correct_answer": card["kanji"],
        "next_due": new_state["due"]
    }

@router.get("/lectura-kanji", response_model=LecturaKanjiQuestion)
async def get_lectura_kanji_question():
    """Get a reading to kanji quiz question"""
    cards = load_cards()
    if not cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles")
    
    due_cards = lectura_srs.get_due_cards(cards)
    if not due_cards:
        raise HTTPException(status_code=404, detail="No hay tarjetas pendientes para hoy")
    
    card = random.choice(due_cards)
    reading_type = random.choice(["china", "japonesa"])
    correct_reading = card["lectura_china"] if reading_type == "china" else card["lectura_japonesa"]
    
    if not correct_reading:
        reading_type = "japonesa" if reading_type == "china" else "china"
        correct_reading = card["lectura_china"] if reading_type == "china" else card["lectura_japonesa"]
        if not correct_reading:
            raise HTTPException(status_code=404, detail="No hay lecturas disponibles para este kanji")
    
    choices = generate_choices(cards, card["kanji"], "kanji")
    correct_option = choices.index(card["kanji"]) + 1
    
    # Cache the correct option for this reading
    cache_key = f"{correct_reading}_{reading_type}"
    answer_cache[cache_key] = correct_option
    
    return {
        "kanji": correct_reading,  # Aquí enviamos la lectura como "kanji"
        "options": choices,
        "correct_option": correct_option,
        "reading_type": reading_type
    }

@router.post("/lectura-kanji/answer", response_model=QuizResponse)
async def answer_lectura_kanji(answer: LecturaKanjiAnswer):
    """Process a reading to kanji quiz answer"""
    cards = load_cards()
    
    # Get the correct option from cache
    cache_key = f"{answer.reading_value}_{answer.reading_type}"  # Use either kanji or lectura
    correct_option = answer_cache.get(cache_key)
    if correct_option is None:
        raise HTTPException(status_code=400, detail="Pregunta expirada o inválida")
    
    # Encontrar el kanji que tiene esta lectura
    card = next((c for c in cards if (
        (answer.reading_type == "china" and c["lectura_china"] == answer.reading_value) or
        (answer.reading_type == "japonesa" and c["lectura_japonesa"] == answer.reading_value)
    )), None)
    
    if not card:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    
    quality = 5 if answer.answer == correct_option else 1
    new_state = lectura_srs.update_card(f"{card['id']}_{answer.reading_type}", quality)
    
    # Clean up cache
    answer_cache.pop(cache_key, None)
    
    return {
        "correct": quality == 5,
        "correct_answer": card["kanji"],
        "next_due": new_state["due"]
    } 