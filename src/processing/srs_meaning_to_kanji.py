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
    """Ejecuta el quiz de significado a kanji."""
    cards = load_cards()
    state = load_state(cards)
    due = choose_due(cards, state)
    random.shuffle(due)

    if not due:
        print("No hay tarjetas para repasar hoy.")
        return

    to_repeat = []

    # Pregunta principal: mostrar significado, elegir kanji
    for card in due:
        correct_kanji = card["kanji"]
        meaning = card["meaning"]

        distractors = get_distractors(cards, correct_kanji, lambda c: c["kanji"])
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
            meaning = card["meaning"]

            distractors = get_distractors(cards, correct_kanji, lambda c: c["kanji"])
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