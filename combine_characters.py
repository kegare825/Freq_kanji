import pandas as pd
import os

def combine_character_files():
    """Combina todos los archivos de caracteres en una sola tabla, agrupando por kanji."""
    try:
        # Directorio que contiene los archivos CSV
        data_dir = 'data'
        
        # Verificar que el directorio existe
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"El directorio {data_dir} no existe")
        
        # Lista para almacenar todos los DataFrames
        all_dfs = []
        
        # Procesar cada archivo
        for filename in os.listdir(data_dir):
            if filename.endswith('_characters.csv'):
                # Extraer el nombre de la fuente
                source_name = filename.replace('_characters.csv', '')
                
                # Leer el archivo CSV
                file_path = os.path.join(data_dir, filename)
                print(f"Procesando archivo: {file_path}")
                df = pd.read_csv(file_path)
                
                # Filtrar la fila 'all'
                df = df[df['char'] != 'all']
                
                # Renombrar las columnas para incluir la fuente
                df = df.rename(columns={
                    'code_point_hex': f'code_{source_name}',
                    'char_count': f'count_{source_name}'
                })
                
                # Mantener solo las columnas necesarias
                df = df[['char', f'code_{source_name}', f'count_{source_name}']]
                
                all_dfs.append(df)
        
        if not all_dfs:
            raise ValueError("No se encontraron archivos de caracteres para procesar")
        
        # Combinar todos los DataFrames por el carácter
        combined_df = all_dfs[0]
        for df in all_dfs[1:]:
            combined_df = pd.merge(combined_df, df, on='char', how='outer')
        
        # Rellenar NaN con 0 para los conteos
        count_columns = [col for col in combined_df.columns if col.startswith('count_')]
        combined_df[count_columns] = combined_df[count_columns].fillna(0)
        
        # Ordenar por frecuencia en noticias (puedes cambiar esto al orden que prefieras)
        combined_df = combined_df.sort_values('count_news', ascending=False)
        
        # Guardar el resultado en el directorio data
        output_path = os.path.join(data_dir, 'all_kanji.csv')
        print(f"Guardando archivo en: {output_path}")
        combined_df.to_csv(output_path, index=False)
        
        print(f"Archivos combinados exitosamente en '{output_path}'")
        print(f"Total de kanji únicos: {len(combined_df)}")
        print("\nTop 10 kanji más frecuentes en noticias:")
        print(combined_df[['char', 'code_news', 'count_news', 'code_wikipedia', 'count_wikipedia', 'code_aozora', 'count_aozora']].head(10))
        
    except Exception as e:
        print(f"Error al procesar los archivos: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    combine_character_files() 