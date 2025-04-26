import json
import random
import datetime
import os

# --- CONFIG ---
CARDS_JSON    = "kanji_meanings_readings.json"
STATE_JSON    = "srs_state.json"
NUM_CHOICES   = 5

# SM-2 parameters
MIN_EASINESS     = 1.3
DEFAULT_EASINESS = 2.5

# --- HELPERS ---
def load_cards():
    with open(CARDS_JSON, encoding="utf-8") as f:
        return json.load(f)

def load_state(cards):
    if os.path.exists(STATE_JSON):
        with open(STATE_JSON, encoding="utf-8") as f:
            return json.load(f)
    today = datetime.date.today().isoformat()
    return {
        card['kanji']: {
            "interval": 0,
            "repetitions": 0,
            "easiness": DEFAULT_EASINESS,
            "due": today
        }
        for card in cards
    }

def save_state(state):
    with open(STATE_JSON, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def sm2_update(card_state, quality):
    if quality < 3:
        card_state["repetitions"] = 0
        card_state["interval"]    = 0   # repetir hoy mismo
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

def choose_due(cards, state):
    today = datetime.date.today().isoformat()
    return [c for c in cards if state[c['kanji']]["due"] <= today]

# --- QUIZ LOOP (inverted) ---
def quiz():
    cards = load_cards()
    state = load_state(cards)
    due   = choose_due(cards, state)
    random.shuffle(due)

    if not due:
        print("No hay tarjetas para repasar hoy.")
        return

    to_repeat = []

    # Pregunta principal: mostrar significado, elegir kanji
    for card in due:
        correct_kanji = card["kanji"]
        meaning       = card["meaning"]

        other_kanji = [c["kanji"] for c in cards if c["kanji"] != correct_kanji]
        distractors = random.sample(other_kanji, min(len(other_kanji), NUM_CHOICES-1))
        while len(distractors) < NUM_CHOICES-1:
            distractors.append(" ")
        choices = distractors + [correct_kanji]
        random.shuffle(choices)

        print(f"\nSignificado: {meaning}")
        for i, k in enumerate(choices, 1):
            print(f"  {i}. {k}")

        ans = input("Tu respuesta (número): ")
        try:
            sel = int(ans) - 1
            correct = (choices[sel] == correct_kanji)
        except:
            correct = False

        quality = 5 if correct else 2
        if correct:
            print("¡Correcto!")
        else:
            print(f"Incorrecto. El kanji era: {correct_kanji}")
            to_repeat.append(card)

        state[correct_kanji] = sm2_update(state[correct_kanji], quality)
        print(f"Se repetirá el: {state[correct_kanji]['due']}")
        save_state(state)

    # Repetición de fallos al final de la sesión
    if to_repeat:
        print("\n--- Repetición de fallos ---")
        for card in to_repeat:
            correct_kanji = card["kanji"]
            meaning       = card["meaning"]

            other_kanji = [c["kanji"] for c in cards if c["kanji"] != correct_kanji]
            distractors = random.sample(other_kanji, min(len(other_kanji), NUM_CHOICES-1))
            while len(distractors) < NUM_CHOICES-1:
                distractors.append(" ")
            choices = distractors + [correct_kanji]
            random.shuffle(choices)

            print(f"\nSignificado: {meaning}")
            for i, k in enumerate(choices, 1):
                print(f"  {i}. {k}")

            ans = input("Tu respuesta (número): ")
            try:
                sel = int(ans) - 1
                correct = (choices[sel] == correct_kanji)
            except:
                correct = False

            quality = 5 if correct else 2
            if correct:
                print("¡Correcto esta vez!")
            else:
                print(f"Sigue sin acertar – era: {correct_kanji}")

            state[correct_kanji] = sm2_update(state[correct_kanji], quality)
            print(f"Se repetirá el: {state[correct_kanji]['due']}")
            save_state(state)

if __name__ == "__main__":
    quiz()
