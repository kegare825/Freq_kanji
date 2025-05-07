import json
import random
import datetime
import os
import sqlite3
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.utils.config import DB_PATH, SRS_STATE_SIGNIFICADO_PATH

# --- CONFIG ---
NUM_CHOICES = 5

# SM-2 parameters
MIN_EASINESS = 1.3
DEFAULT_EASINESS = 2.5

# --- HELPERS ---
def load_cards():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT kanji, significado FROM kanji")
    cards = [
        {
            "kanji": row[0],
            "significado": row[1]
        } for row in cursor.fetchall()
    ]
    conn.close()
    return cards

def load_state(cards):
    if os.path.exists(SRS_STATE_SIGNIFICADO_PATH):
        with open(SRS_STATE_SIGNIFICADO_PATH, encoding="utf-8") as f:
            return json.load(f)
    today = datetime.date.today().isoformat()
    return {
        card["kanji"]: {
            "interval": 0,
            "repetitions": 0,
            "easiness": DEFAULT_EASINESS,
            "due": today
        } for card in cards
    }

def save_state(state):
    # Ensure directory exists
    os.makedirs(os.path.dirname(SRS_STATE_SIGNIFICADO_PATH), exist_ok=True)
    with open(SRS_STATE_SIGNIFICADO_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def sm2_update(card_state, quality):
    if quality < 3:
        card_state["repetitions"] = 0
        card_state["interval"] = 0   # repetir hoy
    else:
        if card_state["repetitions"] == 0:
            card_state["interval"] = 1
        elif card_state["repetitions"] == 1:
            card_state["interval"] = 6
        else:
            card_state["interval"] = round(card_state["interval"] * card_state["easiness"])
        card_state["repetitions"] += 1

    # actualizar facilidad
    ef = card_state["easiness"] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    card_state["easiness"] = max(MIN_EASINESS, ef)

    next_due = datetime.date.today() + datetime.timedelta(days=card_state["interval"])
    card_state["due"] = next_due.isoformat()
    return card_state

def choose_due(cards, state):
    today = datetime.date.today().isoformat()
    return [c for c in cards if state[c['kanji']]["due"] <= today]

# --- QUIZ LOOP ---
def quiz():
    cards = load_cards()
    state = load_state(cards)
    due = choose_due(cards, state)
    random.shuffle(due)

    if not due:
        print("No hay tarjetas para repasar hoy.")
        return

    # Lista para re-preguntar las falladas
    to_repeat = []

    # Ronda principal
    for card in due:
        kanji, meaning = card["kanji"], card["significado"]
        other = [c["significado"] for c in cards if c["significado"] != meaning]
        distractors = random.sample(other, min(len(other), NUM_CHOICES-1))
        while len(distractors) < NUM_CHOICES-1:
            distractors.append("")
        choices = distractors + [meaning]
        random.shuffle(choices)

        print(f"\nKanji: {kanji}")
        for i, ch in enumerate(choices,1):
            print(f"  {i}. {ch}")
        ans = input("Tu respuesta: ")
        try:
            correct = (choices[int(ans)-1] == meaning)
        except:
            correct = False

        quality = 5 if correct else 2
        if not correct:
            print(f"Incorrecto – respuesta: {meaning}")
            to_repeat.append(card)
        else:
            print("¡Correcto!")

        state[kanji] = sm2_update(state[kanji], quality)
        print(f"Se repetirá el: {state[kanji]['due']}")
        save_state(state)

    # Ronda de repetición de fallos
    if to_repeat:
        print("\n--- Repetición de fallos ---")
        for card in to_repeat:
            kanji, meaning = card["kanji"], card["significado"]
            # misma lógica de opciones
            other = [c["significado"] for c in cards if c["significado"] != meaning]
            distractors = random.sample(other, min(len(other), NUM_CHOICES-1))
            while len(distractors) < NUM_CHOICES-1:
                distractors.append("")
            choices = distractors + [meaning]
            random.shuffle(choices)

            print(f"\nKanji: {kanji}")
            for i, ch in enumerate(choices,1):
                print(f"  {i}. {ch}")
            ans = input("Tu respuesta: ")
            try:
                correct = (choices[int(ans)-1] == meaning)
            except:
                correct = False

            quality = 5 if correct else 2
            if not correct:
                print(f"Sigue sin acertar – respuesta: {meaning}")
            else:
                print("¡Correcto esta vez!")
            state[kanji] = sm2_update(state[kanji], quality)
            print(f"Se repetirá el: {state[kanji]['due']}")
            save_state(state)

if __name__ == "__main__":
    quiz()
