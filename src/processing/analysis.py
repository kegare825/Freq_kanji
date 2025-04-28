import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logger = logging.getLogger(__name__)

def analyze_frequency(df):
    """
    Realiza análisis de frecuencia:
    - Calcula estadísticas básicas
    - Genera gráficos de distribución
    """
    try:
        # Estadísticas básicas
        stats = df['frequency'].describe()
        logger.info(f"Estadísticas de frecuencia:\n{stats}")
        
        # Gráfico de distribución
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df, x='frequency', bins=50)
        plt.title('Distribución de Frecuencia de Kanjis')
        plt.xlabel('Frecuencia')
        plt.ylabel('Cantidad')
        plt.savefig('frequency_distribution.png')
        plt.close()
        
        return stats
    except Exception as e:
        logger.error(f"Error en análisis de frecuencia: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Ejemplo de uso
    df = pd.DataFrame({
        'char': ['一', '二', '三'],
        'frequency': [100, 200, 300]
    })
    stats = analyze_frequency(df)
    print(stats) 