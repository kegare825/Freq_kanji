import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

def parse_csv_files():
    """Procesa los archivos CSV de kanji y documentos"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    
    # Procesar archivos de caracteres
    for source in ['aozora', 'news', 'wikipedia']:
        try:
            df = pd.read_csv(os.path.join(data_dir, f'{source}_characters.csv'))
            logger.info(f"Procesado {source}_characters.csv: {len(df)} registros")
        except Exception as e:
            logger.error(f"Error al procesar {source}_characters.csv: {str(e)}")
    
    # Procesar archivos de documentos
    for source in ['aozora', 'news', 'wikipedia']:
        try:
            df = pd.read_csv(os.path.join(data_dir, f'{source}_documents.csv'))
            logger.info(f"Procesado {source}_documents.csv: {len(df)} registros")
        except Exception as e:
            logger.error(f"Error al procesar {source}_documents.csv: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parse_csv_files() 