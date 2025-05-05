import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os

logger = logging.getLogger(__name__)

def analyze_frequency():
    """
    Realiza análisis de frecuencia:
    - Calcula estadísticas básicas
    - Genera gráficos de distribución
    """
    try:
        # Obtener la ruta al archivo CSV
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        csv_path = os.path.join(data_dir, 'kanji_combined.csv')
        
        # Leer el archivo CSV
        df = pd.read_csv(csv_path)
        
        # Estadísticas básicas
        stats = df['frequency'].describe()
        logger.info(f"Estadísticas de frecuencia:\n{stats}")
        
        # Gráfico de distribución
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df, x='frequency', bins=50)
        plt.title('Distribución de Frecuencia de Kanjis')
        plt.xlabel('Frecuencia')
        plt.ylabel('Cantidad')
        plt.savefig(os.path.join(data_dir, 'frequency_distribution.png'))
        plt.close()
        
        return stats
    except Exception as e:
        logger.error(f"Error en análisis de frecuencia: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    stats = analyze_frequency()
    print(stats) 