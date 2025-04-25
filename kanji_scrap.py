import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import json
import time
import pandas as pd

# Leer el CSV y extraer la columna 'char'
df = pd.read_csv('all_kanji.csv')
kanji_list = df['char'].dropna().unique().tolist()[:5]   # Eliminamos NaNs y duplicados

# URL base del sitio
BASE_URL = "https://japonesbasico.com/kanji/"

# Lista para almacenar los datos extraídos
kanji_data = []

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
        
        time.sleep(1)
        
    except Exception as e:
        print(f"Error al procesar el kanji {kanji}: {e}")

with open('kanji_data.json', 'w', encoding='utf-8') as f:
    json.dump(kanji_data, f, ensure_ascii=False, indent=4)

print("Extracción completada. Datos guardados en 'kanji_data.json'.")
