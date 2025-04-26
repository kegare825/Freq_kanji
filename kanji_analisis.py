import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_cumulative_frequency():
    # Leer el archivo combinado
    df = pd.read_csv('data/kanji_combined.csv')
    
    # Crear figura con subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Limitar a 2000 kanjis
    max_kanji = 2000
    
    # Calcular frecuencias acumuladas para caracteres por fuente
    df_sorted = df.sort_values('total_char_freq', ascending=False)
    kanji_count = np.arange(1, min(len(df_sorted), max_kanji) + 1)
    
    # Aozora
    aozora_sorted = df.sort_values('aozora_char_freq', ascending=False)
    aozora_cumulative = aozora_sorted['aozora_char_freq'].cumsum()[:max_kanji]
    
    # News
    news_sorted = df.sort_values('news_char_freq', ascending=False)
    news_cumulative = news_sorted['news_char_freq'].cumsum()[:max_kanji]
    
    # Wikipedia
    wiki_sorted = df.sort_values('wiki_char_freq', ascending=False)
    wiki_cumulative = wiki_sorted['wiki_char_freq'].cumsum()[:max_kanji]
    
    # Total
    total_cumulative = df_sorted['total_char_freq'].cumsum()[:max_kanji]
    
    # Gráfico de frecuencia acumulada de caracteres
    ax1.plot(kanji_count, aozora_cumulative * 100, 'b-', label='Aozora')
    ax1.plot(kanji_count, news_cumulative * 100, 'g-', label='News')
    ax1.plot(kanji_count, wiki_cumulative * 100, 'r-', label='Wikipedia')
    ax1.plot(kanji_count, total_cumulative * 100, 'k--', label='Total')
    
    ax1.set_title('Frecuencia Acumulada de Caracteres (primeros 2000 kanjis)')
    ax1.set_xlabel('Número de Kanjis')
    ax1.set_ylabel('Porcentaje de Cobertura (%)')
    ax1.grid(True)
    ax1.legend()
    
    # Añadir líneas de referencia para puntos importantes
    for percentage in [50, 80, 90, 95]:
        idx = np.argmax(total_cumulative >= percentage/100)
        ax1.axvline(x=kanji_count[idx], color='k', linestyle='--', alpha=0.3)
        ax1.axhline(y=percentage, color='k', linestyle='--', alpha=0.3)
        ax1.text(kanji_count[idx], percentage, 
                f'{kanji_count[idx]} kanjis\n({percentage}%)',
                ha='right', va='bottom')
    
    # Calcular frecuencias acumuladas para documentos por fuente
    df_sorted_doc = df.sort_values('total_doc_freq', ascending=False)
    kanji_count_doc = np.arange(1, min(len(df_sorted_doc), max_kanji) + 1)
    
    # Aozora
    aozora_doc_sorted = df.sort_values('aozora_doc_freq', ascending=False)
    aozora_doc_cumulative = aozora_doc_sorted['aozora_doc_freq'].cumsum()[:max_kanji]
    
    # News
    news_doc_sorted = df.sort_values('news_doc_freq', ascending=False)
    news_doc_cumulative = news_doc_sorted['news_doc_freq'].cumsum()[:max_kanji]
    
    # Wikipedia
    wiki_doc_sorted = df.sort_values('wiki_doc_freq', ascending=False)
    wiki_doc_cumulative = wiki_doc_sorted['wiki_doc_freq'].cumsum()[:max_kanji]
    
    # Total
    total_doc_cumulative = df_sorted_doc['total_doc_freq'].cumsum()[:max_kanji]
    
    # Gráfico de frecuencia acumulada de documentos
    ax2.plot(kanji_count_doc, aozora_doc_cumulative * 100, 'b-', label='Aozora')
    ax2.plot(kanji_count_doc, news_doc_cumulative * 100, 'g-', label='News')
    ax2.plot(kanji_count_doc, wiki_doc_cumulative * 100, 'r-', label='Wikipedia')
    ax2.plot(kanji_count_doc, total_doc_cumulative * 100, 'k--', label='Total')
    
    ax2.set_title('Frecuencia Acumulada de Documentos (primeros 2000 kanjis)')
    ax2.set_xlabel('Número de Kanjis')
    ax2.set_ylabel('Porcentaje de Cobertura (%)')
    ax2.grid(True)
    ax2.legend()
    
    # Añadir líneas de referencia para puntos importantes
    for percentage in [50, 80, 90, 95]:
        idx = np.argmax(total_doc_cumulative >= percentage/100)
        ax2.axvline(x=kanji_count_doc[idx], color='k', linestyle='--', alpha=0.3)
        ax2.axhline(y=percentage, color='k', linestyle='--', alpha=0.3)
        ax2.text(kanji_count_doc[idx], percentage, 
                f'{kanji_count_doc[idx]} kanjis\n({percentage}%)',
                ha='right', va='bottom')
    
    # Ajustar el layout y guardar
    plt.tight_layout()
    plt.savefig('data/kanji_frequency_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Imprimir estadísticas importantes
    print("\nEstadísticas de cobertura de caracteres (primeros 2000 kanjis):")
    for percentage in [50, 80, 90, 95]:
        idx = np.argmax(total_cumulative >= percentage/100)
        print(f"Para cubrir el {percentage}% de los caracteres, necesitas conocer {kanji_count[idx]} kanjis")
    
    print("\nEstadísticas de cobertura de documentos (primeros 2000 kanjis):")
    for percentage in [50, 80, 90, 95]:
        idx = np.argmax(total_doc_cumulative >= percentage/100)
        print(f"Para cubrir el {percentage}% de los documentos, necesitas conocer {kanji_count_doc[idx]} kanjis")

if __name__ == "__main__":
    plot_cumulative_frequency() 