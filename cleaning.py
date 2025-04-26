import json

# 1) Carga el JSON original
with open("kanji_data.json", encoding="utf-8") as f:
    data = json.load(f)

cleaned = []
for entry in data:
    content = entry.get("content", "")
    # 2) Cortar a partir de la sección de palabras (marcada por "Palabras")
    #    Conservamos todo lo anterior, eliminamos lo que sigue
    cut_point = content.find("Palabras")
    if cut_point != -1:
        content_no_words = content[:cut_point].rstrip()
    else:
        content_no_words = content

    # 3) Construir nueva entrada sin las palabras
    cleaned.append({
        "kanji": entry["kanji"],
        "url": entry["url"],
        "content": content_no_words
    })

# 4) Volcar a un nuevo JSON
with open("kanji_data_no_words.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"Procesadas {len(cleaned)} kanji, creado kanji_data_no_words.json")
