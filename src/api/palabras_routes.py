from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
import sqlite3
import random
from pathlib import Path
from src.services.srs_service import SRSService

router = APIRouter(prefix="/palabras", tags=["palabras"])

# Rutas de acceso a datos
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
DB_PATH = DATA_DIR / 'kanji.db'

# Inicializar servicios SRS para palabras
palabra_significado_srs = SRSService(DATA_DIR / 'srs_state_palabra_significado.json')
significado_palabra_srs = SRSService(DATA_DIR / 'srs_state_significado_palabra.json')

# Cache para almacenar respuestas correctas
answer_cache: Dict[str, int] = {}

# Modelos
class PalabraItem(BaseModel):
    id: int
    frecuencia: int
    palabra: str
    significado: str

class PalabrasResponse(BaseModel):
    total: int
    items: List[PalabraItem]

class QuizQuestion(BaseModel):
    palabra: str
    options: List[str]
    correct_option: int

class QuizResponse(BaseModel):
    correct: bool
    correct_answer: str
    next_due: str

class PalabraAnswer(BaseModel):
    palabra: str
    answer: int

class SignificadoQuestion(BaseModel):
    significado: str
    options: List[str]
    correct_option: int

class SignificadoAnswer(BaseModel):
    significado: str
    answer: int

def connect_db():
    """Crea una conexión a la base de datos"""
    return sqlite3.connect(DB_PATH)

def load_palabras():
    """Carga las palabras frecuentes desde la base de datos"""
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, frecuencia, palabra, significado FROM palabras_frecuentes")
    palabras = [
        {
            "id": row[0],
            "frecuencia": row[1],
            "palabra": row[2],
            "significado": row[3]
        } for row in cursor.fetchall()
    ]
    conn.close()
    
    return palabras

def generate_choices(items: List[Dict], target: str, field: str = "significado") -> List[str]:
    """Genera opciones para el quiz"""
    all_options = [item[field] for item in items if item[field]]
    unique_options = list(set(all_options) - {target})
    
    if len(unique_options) < 3:
        return [target]  # Si no hay suficientes opciones, solo devuelve la correcta
    
    choices = random.sample(unique_options, min(3, len(unique_options)))
    choices.append(target)
    random.shuffle(choices)
    return choices

@router.get("/buscar-por-palabra", response_model=PalabrasResponse)
async def buscar_por_palabra(
    palabra: str = Query(..., description="Texto de la palabra japonesa a buscar"),
    limit: int = Query(10, description="Número máximo de resultados")
):
    """
    Busca palabras japonesas que contienen el texto especificado
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    # Buscar palabras que contengan el texto (usando LIKE)
    query = "SELECT id, frecuencia, palabra, significado FROM palabras_frecuentes WHERE palabra LIKE ? ORDER BY frecuencia LIMIT ?"
    cursor.execute(query, (f"%{palabra}%", limit))
    
    rows = cursor.fetchall()
    
    # Obtener el total de coincidencias (sin el límite)
    cursor.execute("SELECT COUNT(*) FROM palabras_frecuentes WHERE palabra LIKE ?", (f"%{palabra}%",))
    total = cursor.fetchone()[0]
    
    conn.close()
    
    # Convertir a modelo de datos
    items = [
        PalabraItem(id=row[0], frecuencia=row[1], palabra=row[2], significado=row[3])
        for row in rows
    ]
    
    return PalabrasResponse(total=total, items=items)

@router.get("/buscar-por-significado", response_model=PalabrasResponse)
async def buscar_por_significado(
    significado: str = Query(..., description="Texto del significado a buscar"),
    limit: int = Query(10, description="Número máximo de resultados")
):
    """
    Busca palabras japonesas por su significado
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    # Buscar por significado (usando LIKE)
    query = "SELECT id, frecuencia, palabra, significado FROM palabras_frecuentes WHERE significado LIKE ? ORDER BY frecuencia LIMIT ?"
    cursor.execute(query, (f"%{significado}%", limit))
    
    rows = cursor.fetchall()
    
    # Obtener el total de coincidencias (sin el límite)
    cursor.execute("SELECT COUNT(*) FROM palabras_frecuentes WHERE significado LIKE ?", (f"%{significado}%",))
    total = cursor.fetchone()[0]
    
    conn.close()
    
    # Convertir a modelo de datos
    items = [
        PalabraItem(id=row[0], frecuencia=row[1], palabra=row[2], significado=row[3])
        for row in rows
    ]
    
    return PalabrasResponse(total=total, items=items)

@router.get("/top", response_model=PalabrasResponse)
async def obtener_top_palabras(
    limit: int = Query(50, description="Número máximo de palabras a mostrar")
):
    """
    Obtiene las palabras más frecuentes ordenadas por frecuencia
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    # Obtener las palabras más frecuentes
    query = "SELECT id, frecuencia, palabra, significado FROM palabras_frecuentes ORDER BY frecuencia LIMIT ?"
    cursor.execute(query, (limit,))
    
    rows = cursor.fetchall()
    
    # Obtener el total de palabras
    cursor.execute("SELECT COUNT(*) FROM palabras_frecuentes")
    total = cursor.fetchone()[0]
    
    conn.close()
    
    # Convertir a modelo de datos
    items = [
        PalabraItem(id=row[0], frecuencia=row[1], palabra=row[2], significado=row[3])
        for row in rows
    ]
    
    return PalabrasResponse(total=total, items=items)

@router.get("/quiz/palabra-significado", response_model=QuizQuestion)
async def get_palabra_significado_question():
    """
    Obtiene una pregunta de quiz: palabra -> significado
    """
    palabras = load_palabras()
    if not palabras:
        raise HTTPException(status_code=404, detail="No hay palabras disponibles")
    
    due_palabras = palabra_significado_srs.get_due_cards(palabras)
    if not due_palabras:
        # Si no hay palabras pendientes, usa las más frecuentes para empezar
        due_palabras = sorted(palabras, key=lambda x: x["frecuencia"])[:50]
        if not due_palabras:
            raise HTTPException(status_code=404, detail="No hay palabras pendientes para hoy")
    
    # Seleccionar una palabra aleatoria entre las pendientes
    palabra = random.choice(due_palabras)
    choices = generate_choices(palabras, palabra["significado"], "significado")
    correct_option = choices.index(palabra["significado"]) + 1
    
    # Almacenar la opción correcta en caché
    answer_cache[palabra["palabra"]] = correct_option
    
    return {
        "palabra": palabra["palabra"],
        "options": choices,
        "correct_option": correct_option
    }

@router.post("/quiz/palabra-significado/answer", response_model=QuizResponse)
async def answer_palabra_significado(answer: PalabraAnswer):
    """
    Procesa la respuesta a una pregunta palabra -> significado
    """
    palabras = load_palabras()
    palabra = next((p for p in palabras if p["palabra"] == answer.palabra), None)
    if not palabra:
        raise HTTPException(status_code=404, detail="Palabra no encontrada")
    
    # Obtener la opción correcta de la caché
    correct_option = answer_cache.get(answer.palabra)
    if correct_option is None:
        raise HTTPException(status_code=400, detail="Pregunta expirada o inválida")
    
    quality = 5 if answer.answer == correct_option else 1
    new_state = palabra_significado_srs.update_card(str(palabra["id"]), quality)
    
    # Limpiar caché
    answer_cache.pop(answer.palabra, None)
    
    return {
        "correct": quality == 5,
        "correct_answer": palabra["significado"],
        "next_due": new_state["due"]
    }

@router.get("/quiz/significado-palabra", response_model=SignificadoQuestion)
async def get_significado_palabra_question():
    """
    Obtiene una pregunta de quiz: significado -> palabra
    """
    palabras = load_palabras()
    if not palabras:
        raise HTTPException(status_code=404, detail="No hay palabras disponibles")
    
    due_palabras = significado_palabra_srs.get_due_cards(palabras)
    if not due_palabras:
        # Si no hay palabras pendientes, usa las más frecuentes para empezar
        due_palabras = sorted(palabras, key=lambda x: x["frecuencia"])[:50]
        if not due_palabras:
            raise HTTPException(status_code=404, detail="No hay palabras pendientes para hoy")
    
    # Seleccionar una palabra aleatoria entre las pendientes
    palabra = random.choice(due_palabras)
    choices = generate_choices(palabras, palabra["palabra"], "palabra")
    correct_option = choices.index(palabra["palabra"]) + 1
    
    # Almacenar la opción correcta en caché
    answer_cache[palabra["significado"]] = correct_option
    
    return {
        "significado": palabra["significado"],
        "options": choices,
        "correct_option": correct_option
    }

@router.post("/quiz/significado-palabra/answer", response_model=QuizResponse)
async def answer_significado_palabra(answer: SignificadoAnswer):
    """
    Procesa la respuesta a una pregunta significado -> palabra
    """
    palabras = load_palabras()
    palabra = next((p for p in palabras if p["significado"] == answer.significado), None)
    if not palabra:
        raise HTTPException(status_code=404, detail="Significado no encontrado")
    
    # Obtener la opción correcta de la caché
    correct_option = answer_cache.get(answer.significado)
    if correct_option is None:
        raise HTTPException(status_code=400, detail="Pregunta expirada o inválida")
    
    quality = 5 if answer.answer == correct_option else 1
    new_state = significado_palabra_srs.update_card(str(palabra["id"]), quality)
    
    # Limpiar caché
    answer_cache.pop(answer.significado, None)
    
    return {
        "correct": quality == 5,
        "correct_answer": palabra["palabra"],
        "next_due": new_state["due"]
    } 