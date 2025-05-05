import random
import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.processing.srs_utils import (
    load_cards, load_state, save_state, sm2_update,
    choose_due, get_distractors
)

def quiz():
    """Ejecuta el quiz de kanji a significado."""
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
        kanji, meaning = card["kanji"], card["meaning"]
        distractors = get_distractors(cards, meaning, lambda c: c["meaning"])
        choices = distractors + [meaning]
        random.shuffle(choices)

        print(f"\nKanji: {kanji}")
        for i, ch in enumerate(choices, 1):
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
            kanji, meaning = card["kanji"], card["meaning"]
            distractors = get_distractors(cards, meaning, lambda c: c["meaning"])
            choices = distractors + [meaning]
            random.shuffle(choices)

            print(f"\nKanji: {kanji}")
            for i, ch in enumerate(choices, 1):
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