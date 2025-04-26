import pandas as pd
import os

def combine_kanji_data():
    # Leer todos los archivos CSV
    aozora_chars = pd.read_csv('data/aozora_characters.csv')
    aozora_docs = pd.read_csv('data/aozora_documents.csv')
    news_chars = pd.read_csv('data/news_characters.csv')
    news_docs = pd.read_csv('data/news_documents.csv')
    wiki_chars = pd.read_csv('data/wikipedia_characters.csv')
    wiki_docs = pd.read_csv('data/wikipedia_documents.csv')
    
    # Renombrar las columnas para identificar la fuente
    aozora_chars = aozora_chars.rename(columns={'char_count': 'aozora_char_count'})
    aozora_docs = aozora_docs.rename(columns={'doc_count': 'aozora_doc_count'})
    news_chars = news_chars.rename(columns={'char_count': 'news_char_count'})
    news_docs = news_docs.rename(columns={'doc_count': 'news_doc_count'})
    wiki_chars = wiki_chars.rename(columns={'char_count': 'wiki_char_count'})
    wiki_docs = wiki_docs.rename(columns={'doc_count': 'wiki_doc_count'})
    
    # Hacer outer join de todos los dataframes usando 'char' como clave
    # Primero unimos los archivos de characters
    combined = pd.merge(aozora_chars[['char', 'aozora_char_count']], 
                       news_chars[['char', 'news_char_count']], 
                       on='char', 
                       how='outer')
    
    combined = pd.merge(combined,
                       wiki_chars[['char', 'wiki_char_count']],
                       on='char',
                       how='outer')
    
    # Luego unimos los archivos de documents
    combined = pd.merge(combined,
                       aozora_docs[['char', 'aozora_doc_count']],
                       on='char',
                       how='outer')
    
    combined = pd.merge(combined,
                       news_docs[['char', 'news_doc_count']],
                       on='char',
                       how='outer')
    
    combined = pd.merge(combined,
                       wiki_docs[['char', 'wiki_doc_count']],
                       on='char',
                       how='outer')
    
    # Rellenar NaN con 0
    combined = combined.fillna(0)
    
    # Calcular totales
    combined['total_char_count'] = combined['aozora_char_count'] + combined['news_char_count'] + combined['wiki_char_count']
    combined['total_doc_count'] = combined['aozora_doc_count'] + combined['news_doc_count'] + combined['wiki_doc_count']
    
    # Calcular frecuencias relativas para cada fuente
    # Frecuencia de caracteres
    total_aozora_chars = combined['aozora_char_count'].sum()
    total_news_chars = combined['news_char_count'].sum()
    total_wiki_chars = combined['wiki_char_count'].sum()
    
    combined['aozora_char_freq'] = combined['aozora_char_count'] / total_aozora_chars
    combined['news_char_freq'] = combined['news_char_count'] / total_news_chars
    combined['wiki_char_freq'] = combined['wiki_char_count'] / total_wiki_chars
    
    # Frecuencia de documentos
    total_aozora_docs = combined['aozora_doc_count'].sum()
    total_news_docs = combined['news_doc_count'].sum()
    total_wiki_docs = combined['wiki_doc_count'].sum()
    
    combined['aozora_doc_freq'] = combined['aozora_doc_count'] / total_aozora_docs
    combined['news_doc_freq'] = combined['news_doc_count'] / total_news_docs
    combined['wiki_doc_freq'] = combined['wiki_doc_count'] / total_wiki_docs
    
    # Frecuencia total
    combined['total_char_freq'] = combined['total_char_count'] / combined['total_char_count'].sum()
    combined['total_doc_freq'] = combined['total_doc_count'] / combined['total_doc_count'].sum()
    
    # Ordenar por total_char_count descendente
    combined = combined.sort_values('total_char_count', ascending=False)
    
    # Guardar el resultado
    output_file = 'data/kanji_combined.csv'
    combined.to_csv(output_file, index=False)
    print(f"Archivo combinado guardado como: {output_file}")
    print(f"Dimensiones del archivo final: {combined.shape}")
    
    # Mostrar las primeras filas para verificación
    print("\nPrimeras filas del archivo combinado:")
    print(combined.head())

if __name__ == "__main__":
    combine_kanji_data() 