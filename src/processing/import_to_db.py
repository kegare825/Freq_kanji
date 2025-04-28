import sqlite3
import pandas as pd
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def print_top_10(conn, table_name):
    """Imprime los 10 primeros registros de una tabla"""
    print(f"\nTop 10 de la tabla {table_name}:")
    query = f"SELECT * FROM {table_name} LIMIT 10"
    df = pd.read_sql_query(query, conn)
    print(df.to_string())
    print("\n" + "="*80 + "\n")

def create_database():
    # Obtener la ruta de la base de datos
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'kanji_data.db')
    
    # Conectar a la base de datos (se crea si no existe)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tabla para datos de caracteres
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS characters (
        char TEXT PRIMARY KEY,
        aozora_char_count INTEGER,
        news_char_count INTEGER,
        wiki_char_count INTEGER,
        aozora_char_freq REAL,
        news_char_freq REAL,
        wiki_char_freq REAL
    )
    ''')
    
    # Crear tabla para datos de documentos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        char TEXT PRIMARY KEY,
        aozora_doc_count INTEGER,
        news_doc_count INTEGER,
        wiki_doc_count INTEGER,
        aozora_doc_freq REAL,
        news_doc_freq REAL,
        wiki_doc_freq REAL
    )
    ''')
    
    # Crear tabla para datos combinados
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS combined (
        char TEXT PRIMARY KEY,
        aozora_char_count INTEGER,
        news_char_count INTEGER,
        wiki_char_count INTEGER,
        aozora_doc_count INTEGER,
        news_doc_count INTEGER,
        wiki_doc_count INTEGER,
        total_char_count INTEGER,
        total_doc_count INTEGER,
        aozora_char_freq REAL,
        news_char_freq REAL,
        wiki_char_freq REAL,
        aozora_doc_freq REAL,
        news_doc_freq REAL,
        wiki_doc_freq REAL,
        total_char_freq REAL,
        total_doc_freq REAL
    )
    ''')
    
    # Importar datos de caracteres
    logger.info("Importando datos de caracteres...")
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    
    aozora_chars = pd.read_csv(os.path.join(data_dir, 'aozora_characters.csv'))
    news_chars = pd.read_csv(os.path.join(data_dir, 'news_characters.csv'))
    wiki_chars = pd.read_csv(os.path.join(data_dir, 'wikipedia_characters.csv'))
    
    # Preparar datos de caracteres
    chars_data = pd.DataFrame()
    chars_data['char'] = pd.concat([
        aozora_chars['char'],
        news_chars['char'],
        wiki_chars['char']
    ]).drop_duplicates()
    
    # Añadir conteos de cada fuente
    chars_data = pd.merge(
        chars_data,
        aozora_chars[['char', 'char_count']].rename(columns={'char_count': 'aozora_char_count'}),
        on='char',
        how='left'
    )
    chars_data = pd.merge(
        chars_data,
        news_chars[['char', 'char_count']].rename(columns={'char_count': 'news_char_count'}),
        on='char',
        how='left'
    )
    chars_data = pd.merge(
        chars_data,
        wiki_chars[['char', 'char_count']].rename(columns={'char_count': 'wiki_char_count'}),
        on='char',
        how='left'
    )
    
    # Calcular frecuencias
    total_aozora = chars_data['aozora_char_count'].sum()
    total_news = chars_data['news_char_count'].sum()
    total_wiki = chars_data['wiki_char_count'].sum()
    
    chars_data['aozora_char_freq'] = chars_data['aozora_char_count'] / total_aozora
    chars_data['news_char_freq'] = chars_data['news_char_count'] / total_news
    chars_data['wiki_char_freq'] = chars_data['wiki_char_count'] / total_wiki
    
    # Importar a la base de datos
    chars_data.to_sql('characters', conn, if_exists='replace', index=False)
    
    # Importar datos de documentos
    logger.info("Importando datos de documentos...")
    aozora_docs = pd.read_csv(os.path.join(data_dir, 'aozora_documents.csv'))
    news_docs = pd.read_csv(os.path.join(data_dir, 'news_documents.csv'))
    wiki_docs = pd.read_csv(os.path.join(data_dir, 'wikipedia_documents.csv'))
    
    # Preparar datos de documentos
    docs_data = pd.DataFrame()
    docs_data['char'] = pd.concat([
        aozora_docs['char'],
        news_docs['char'],
        wiki_docs['char']
    ]).drop_duplicates()
    
    # Añadir conteos de cada fuente
    docs_data = pd.merge(
        docs_data,
        aozora_docs[['char', 'doc_count']].rename(columns={'doc_count': 'aozora_doc_count'}),
        on='char',
        how='left'
    )
    docs_data = pd.merge(
        docs_data,
        news_docs[['char', 'doc_count']].rename(columns={'doc_count': 'news_doc_count'}),
        on='char',
        how='left'
    )
    docs_data = pd.merge(
        docs_data,
        wiki_docs[['char', 'doc_count']].rename(columns={'doc_count': 'wiki_doc_count'}),
        on='char',
        how='left'
    )
    
    # Calcular frecuencias
    total_aozora_docs = docs_data['aozora_doc_count'].sum()
    total_news_docs = docs_data['news_doc_count'].sum()
    total_wiki_docs = docs_data['wiki_doc_count'].sum()
    
    docs_data['aozora_doc_freq'] = docs_data['aozora_doc_count'] / total_aozora_docs
    docs_data['news_doc_freq'] = docs_data['news_doc_count'] / total_news_docs
    docs_data['wiki_doc_freq'] = docs_data['wiki_doc_count'] / total_wiki_docs
    
    # Importar a la base de datos
    docs_data.to_sql('documents', conn, if_exists='replace', index=False)
    
    # Importar datos combinados
    logger.info("Importando datos combinados...")
    combined_data = pd.read_csv(os.path.join(data_dir, 'kanji_combined.csv'))
    combined_data.to_sql('combined', conn, if_exists='replace', index=False)
    
    # Crear índices para mejorar el rendimiento
    logger.info("Creando índices...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_characters_char ON characters(char)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_char ON documents(char)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_combined_char ON combined(char)')
    
    # Mostrar los 10 primeros registros de cada tabla
    logger.info("\nMostrando los 10 primeros registros de cada tabla:")
    print_top_10(conn, 'characters')
    print_top_10(conn, 'documents')
    print_top_10(conn, 'combined')
    
    # Guardar cambios y cerrar conexión
    conn.commit()
    conn.close()
    
    logger.info("Base de datos creada exitosamente!")

if __name__ == "__main__":
    create_database() 