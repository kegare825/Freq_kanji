import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import json
import time
import pandas as pd

# Leer el CSV y extraer la columna 'char'
df = pd.read_csv('data/kanji_combined.csv')
kanji_list = df['char'].tolist()[:10]  # Eliminamos NaNs y duplicados

# URL base del sitio
BASE_URL = "https://japonesbasico.com/kanji/"

# Lista para almacenar los datos extraídos
kanji_data = []
failed_kanji = []

for kanji in kanji_list:
    encoded_kanji = quote(kanji)
    url = f"{BASE_URL}{encoded_kanji}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        texts = soup.stripped_strings
        full_text = '\n'.join(texts)

        kanji_info = {
            'kanji': kanji,
            'url': url,
            'content': full_text
        }
        kanji_data.append(kanji_info)
        print(f"Procesado correctamente: {kanji}")

    except Exception as e:
        print(f"Error al procesar el kanji {kanji}: {e}")
        failed_kanji.append({
            'kanji': kanji,
            'error': str(e)
        })

# Guardar los datos exitosos
with open('kanji_data.json', 'w', encoding='utf-8') as f:
    json.dump(kanji_data, f, ensure_ascii=False, indent=4)

# Guardar los errores
with open('failed_kanji.json', 'w', encoding='utf-8') as f:
    json.dump(failed_kanji, f, ensure_ascii=False, indent=4)

print("\nResumen de la extracción:")
print(f"Total de kanji procesados: {len(kanji_list)}")
print(f"Kanji exitosos: {len(kanji_data)}")
print(f"Kanji fallidos: {len(failed_kanji)}")

if failed_kanji:
    print("\nLista de kanji que fallaron:")
    for error in failed_kanji:
        print(f"- {error['kanji']}: {error['error']}")

print("\nDatos guardados en 'kanji_data.json'")
print("Errores guardados en 'failed_kanji.json'")
