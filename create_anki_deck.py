import pandas as pd
import genanki
import random
import json
import os

def create_anki_deck():
    """Crea un mazo de Anki y un archivo JSON con los kanji ordenados por frecuencia"""
    try:
        # Cargar el archivo CSV con los datos de kanji
        print("Cargando datos de kanji...")
        df = pd.read_csv('data/kanji_complete.csv')
        
        # Ordenar por frecuencia total (suma de las tres fuentes)
        df['total_freq'] = df['count_news'] + df['count_wikipedia'] + df['count_aozora']
        df = df.sort_values('total_freq', ascending=False)
        
        # Crear lista de kanji para JSON
        kanji_list = []
        
        # Crear el modelo de nota
        my_model = genanki.Model(
            random.randrange(1 << 30, 1 << 31),
            'Kanji Model',
            fields=[
                {'name': 'Kanji'},
                {'name': 'Meaning'},
                {'name': 'Readings'},
                {'name': 'Examples'},
                {'name': 'Frequency'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '{{Kanji}}',
                    'afmt': '''
                        <div style="font-size: 30px; text-align: center;">{{Kanji}}</div>
                        <div style="margin: 20px 0;">
                            <strong>Significado:</strong> {{Meaning}}<br>
                            <strong>Lecturas:</strong> {{Readings}}<br>
                            <strong>Ejemplos:</strong> {{Examples}}
                        </div>
                        <div style="margin-top: 20px;">
                            <small>Frecuencia: {{Frequency}}</small>
                        </div>
                    ''',
                },
            ],
            css='''
                .card {
                    font-family: arial;
                    font-size: 20px;
                    text-align: center;
                    color: black;
                    background-color: white;
                }
            '''
        )
        
        # Crear el mazo
        my_deck = genanki.Deck(
            random.randrange(1 << 30, 1 << 31),
            'Japanese::Kanji'
        )
        
        # Procesar cada kanji
        print("Creando tarjetas...")
        for _, row in df.iterrows():
            kanji = row['char']
            
            # Extraer información del contenido si está disponible
            if pd.notna(row['content']):
                content = row['content'].split('\n')
                meaning = content[0].split(' es el kanji de ')[1] if ' es el kanji de ' in content[0] else ''
                readings = content[1] if len(content) > 1 else ''
                examples = content[2] if len(content) > 2 else ''
            else:
                meaning = ''
                readings = ''
                examples = ''
            
            # Crear la nota para Anki
            my_note = genanki.Note(
                model=my_model,
                fields=[
                    kanji,
                    meaning,
                    readings,
                    examples,
                    f"{row['total_freq']:,.0f}"
                ]
            )
            
            # Agregar la nota al mazo
            my_deck.add_note(my_note)
            
            # Agregar kanji a la lista para JSON
            kanji_list.append({
                'kanji': kanji,
                'meaning': meaning,
                'readings': readings,
                'examples': examples,
                'frequency': int(row['total_freq']),
                'count_news': int(row['count_news']),
                'count_wikipedia': int(row['count_wikipedia']),
                'count_aozora': int(row['count_aozora'])
            })
        
        # Guardar el mazo de Anki
        print("Guardando mazo de Anki...")
        genanki.Package(my_deck).write_to_file('data/kanji.apkg')
        
        # Guardar el archivo JSON
        print("Guardando archivo JSON...")
        with open('data/kanji.json', 'w', encoding='utf-8') as f:
            json.dump(kanji_list, f, ensure_ascii=False, indent=2)
        
        print("¡Archivos creados exitosamente!")
        print(f"Total de kanji procesados: {len(df)}")
        print("El mazo de Anki se ha guardado como: data/kanji.apkg")
        print("El archivo JSON se ha guardado como: data/kanji.json")
        
    except Exception as e:
        print(f"Error al crear los archivos: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    create_anki_deck() 