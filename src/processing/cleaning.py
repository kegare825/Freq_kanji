import pandas as pd
import logging

logger = logging.getLogger(__name__)

def clean_data(df):
    """
    Limpia los datos del DataFrame:
    - Elimina filas duplicadas
    - Elimina filas con valores nulos
    - Convierte tipos de datos
    """
    try:
        # Eliminar duplicados
        df = df.drop_duplicates()
        
        # Eliminar filas con valores nulos
        df = df.dropna()
        
        # Convertir tipos de datos
        if 'frequency' in df.columns:
            df['frequency'] = pd.to_numeric(df['frequency'], errors='coerce')
        
        logger.info(f"Datos limpios: {len(df)} registros")
        return df
    except Exception as e:
        logger.error(f"Error al limpiar datos: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Ejemplo de uso
    df = pd.DataFrame({
        'char': ['一', '二', '三'],
        'frequency': [100, 200, 300]
    })
    clean_df = clean_data(df)
    print(clean_df) 