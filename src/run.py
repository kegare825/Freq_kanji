"""
Main script to run the Kanji SRS application.
"""
import sys
import os

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def init_application():
    """Initialize the application and its dependencies."""
    from src.scripts.init_db import init_db
    
    # Initialize the database
    init_db()

def main():
    """Main function to run the application."""
    # Initialize the application
    init_application()
    
    from src.services.srs_kanji_lectura import quiz as quiz_lectura
    from src.services.srs_kanji_significado import quiz as quiz_significado
    
    while True:
        print("\nKanji SRS - Sistema de Repaso Espaciado")
        print("1. Practicar lecturas")
        print("2. Practicar significados")
        print("3. Salir")
        
        choice = input("\nElige una opción: ")
        
        if choice == "1":
            quiz_lectura()
        elif choice == "2":
            quiz_significado()
        elif choice == "3":
            print("¡Hasta luego!")
            break
        else:
            print("Opción no válida. Por favor, elige 1, 2 o 3.")

if __name__ == "__main__":
    main() 