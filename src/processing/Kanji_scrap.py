import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import json
import time
import pandas as pd
import os

# Get the correct path to the CSV file
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
csv_path = os.path.join(data_dir, 'kanji_combined.csv')

# Read the CSV file
df = pd.read_csv(csv_path)
kanji_list = df['char'].tolist()[:50]  # Eliminamos NaNs y duplicados

# URL base del sitio
BASE_URL = "https://japonesbasico.com/kanji/"

# Headers para simular un navegador
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Lista para almacenar los datos extraídos
kanji_data = []
failed_kanji = []

for kanji in kanji_list:
    encoded_kanji = quote(kanji)
    url = f"{BASE_URL}{encoded_kanji}"

    try:
        print(f"Procesando kanji: {kanji}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            print(f"❌ Kanji '{kanji}' no encontrado (404)")
            failed_kanji.append(kanji)
            continue
            
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
        print(f"✓ Kanji '{kanji}' procesado correctamente")

        # Esperar entre peticiones para no sobrecargar el servidor
        time.sleep(2)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al procesar el kanji '{kanji}': {e}")
        failed_kanji.append(kanji)
        continue
    except Exception as e:
        print(f"❌ Error inesperado al procesar el kanji '{kanji}': {e}")
        failed_kanji.append(kanji)
        continue

# Guardar en la carpeta data
output_path = os.path.join(data_dir, 'kanji_data.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(kanji_data, f, ensure_ascii=False, indent=4)

print(f"\nResumen:")
print(f"✓ Extracción completada. Datos guardados en '{output_path}'")
print(f"✓ Kanjis procesados exitosamente: {len(kanji_data)}")
if failed_kanji:
    print(f"❌ Kanjis que fallaron ({len(failed_kanji)}):")
    for kanji in failed_kanji:
        print(f"  - {kanji}")
