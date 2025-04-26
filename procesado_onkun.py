import json
import re

# 1) Carga el JSON original
with open("kanji_data.json", encoding="utf-8") as f:
    data = json.load(f)

output = []
for entry in data:
    text = entry.get("content", "")
    lines = text.splitlines()

    # Extraer significado de la primera línea: "<kanji> es el kanji de <meaning>"
    meaning = None
    m = re.match(r".*es el kanji de (.+)", lines[0])
    if m:
        meaning = m.group(1).strip()
    else:
        # fallback: tomar la segunda non-empty line
        for ln in lines[1:]:
            if ln.strip():
                meaning = ln.strip()
                break

    # Extraer lecturas
    on, kun = None, None
    for i, ln in enumerate(lines):
        if "Lecturas chinas" in ln:
            # siguiente línea no vacía
            for x in lines[i+1:]:
                if x.strip():
                    on = x.strip()
                    break
        if "Lecturas japonesas" in ln:
            for x in lines[i+1:]:
                if x.strip():
                    kun = x.strip()
                    break

    ou
    tput.append({
        "kanji": entry["kanji"],
        "meaning": meaning,
        "lecturas_chinas": on,
        "lecturas_japonesas": kun
    })

# 2) Guardar resultado
with open("kanji_meanings_readings.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("Generado kanji_meanings_readings.json con", len(output), "entradas")
