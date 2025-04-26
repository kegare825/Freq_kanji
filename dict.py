import json
import re

# Ajusta este nombre a tu fichero JSON real
JSON_FILE = "kanji_data.json"

# Carga de datos
with open(JSON_FILE, encoding="utf-8") as f:
    kanji_data = json.load(f)

def split_sections(content):
    partes = re.split(r"Palabras\s+comunes\s+que incluyen este kanji:", content)
    if len(partes) < 2:
        return "", ""
    comun_sec = partes[1]
    partes2 = re.split(r"Palabras\s+no\s+comunes\s+que incluyen este kanji:", comun_sec)
    comunes_text = partes2[0].strip()
    no_comunes_text = partes2[1].strip() if len(partes2) > 1 else ""
    return comunes_text, no_comunes_text

def format_entries(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    entries = []
    i = 0
    while i < len(lines):
        # 1) Compuesto: líneas consecutivas de kanji/kana
        compound_parts = []
        while i < len(lines) and re.match(r"^[\u3000-\u9FFF\u3040-\u30FF]+$", lines[i]):
            compound_parts.append(lines[i])
            i += 1
        if not compound_parts:
            i += 1
            continue
        compound = "".join(compound_parts)

        # 2) Lectura: primer paréntesis con "/" dentro
        reading = ""
        if i < len(lines) and lines[i].startswith("(") and "/" in lines[i]:
            read_parts = []
            # juntar hasta cerrar paréntesis
            while i < len(lines):
                read_parts.append(lines[i].strip("()"))
                if ")" in lines[i]:
                    i += 1
                    break
                i += 1
            reading = " ".join(read_parts)

        # 3) POS: siguiente paréntesis sin "/" 
        pos = ""
        if i < len(lines) and lines[i].startswith("(") and "/" not in lines[i]:
            pos = lines[i].strip("()")
            i += 1

        # 4) Significado: siguiente línea
        meaning = ""
        if i < len(lines):
            meaning = lines[i]
            i += 1

        entries.append((compound, reading, pos, meaning))
    return entries

def mostrar_diccionario(kanji):
    entry = next((e for e in kanji_data if e["kanji"] == kanji), None)
    if not entry:
        print(f"No se encontró información para «{kanji}».")
        return

    print(f"\nDiccionario para {kanji}:\n")
    comunes_text, no_comunes_text = split_sections(entry["content"])
    comunes = format_entries(comunes_text)
    no_comunes = format_entries(no_comunes_text)

    if comunes:
        print("=== Palabras comunes ===")
        for comp, read, pos, mean in comunes:
            print(f"{comp} | lectura: {read} | {pos} | significado: {mean}")
    else:
        print("No hay palabras comunes.")

    if no_comunes:
        print("\n=== Palabras no comunes ===")
        for comp, read, pos, mean in no_comunes:
            print(f"{comp} | lectura: {read} | {pos} | significado: {mean}")
    else:
        print("\nNo hay palabras no comunes.")

if __name__ == "__main__":
    k = input("Introduce un kanji: ")
    mostrar_diccionario(k)
