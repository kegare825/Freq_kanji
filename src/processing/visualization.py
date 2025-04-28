import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import logging

logger = logging.getLogger(__name__)

def plot_frequency_comparison(dfs, sources):
    """
    Genera gráficos comparativos de frecuencia entre diferentes fuentes
    """
    try:
        plt.figure(figsize=(12, 6))
        for df, source in zip(dfs, sources):
            plt.plot(df.index, df['frequency'], label=source)
        
        plt.title('Comparación de Frecuencia de Kanjis por Fuente')
        plt.xlabel('Ranking')
        plt.ylabel('Frecuencia')
        plt.legend()
        plt.grid(True)
        plt.savefig('frequency_comparison.png')
        plt.close()
        
        logger.info("Gráfico de comparación generado exitosamente")
    except Exception as e:
        logger.error(f"Error al generar gráfico de comparación: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Ejemplo de uso
    dfs = [
        pd.DataFrame({
            'char': ['一', '二', '三'],
            'frequency': [100, 200, 300]
        }),
        pd.DataFrame({
            'char': ['一', '二', '三'],
            'frequency': [150, 250, 350]
        })
    ]
    sources = ['Fuente 1', 'Fuente 2']
    plot_frequency_comparison(dfs, sources) 