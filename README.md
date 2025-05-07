# Kanji SRS Application

Una aplicación de Sistema de Repetición Espaciada (SRS) para el aprendizaje de kanji.

## Estructura del Proyecto

```
.
├── src/                    # Código fuente principal
│   ├── api/               # API REST y endpoints
│   ├── models/            # Modelos de datos
│   ├── services/          # Servicios de la aplicación
│   ├── utils/             # Utilidades y funciones auxiliares
│   └── scripts/           # Scripts de utilidad y mantenimiento
├── data/                  # Archivos de datos
│   ├── kanji.db          # Base de datos SQLite
│   ├── kanji_data.json   # Datos de kanji en formato JSON
│   └── srs_states/       # Estados del sistema SRS
└── requirements.txt       # Dependencias del proyecto
```

## Componentes Principales

### API (src/api/)
- Endpoints REST para interactuar con la aplicación
- Gestión de rutas y controladores

### Modelos (src/models/)
- Definiciones de modelos de datos
- Esquemas y validaciones

### Servicios (src/services/)
- Lógica de negocio del SRS
- Servicios de base de datos
- Gestión de kanji y estados

### Utilidades (src/utils/)
- Funciones auxiliares
- Herramientas de limpieza y mantenimiento

### Scripts (src/scripts/)
- Scripts para importación de datos
- Herramientas de mantenimiento
- Scripts de análisis

## Datos (data/)
- Base de datos SQLite con información de kanji
- Archivos JSON con datos adicionales
- Estados del sistema SRS

## Requisitos

```bash
pip install -r requirements.txt
```

## Uso

1. Asegúrate de tener todas las dependencias instaladas
2. Inicia la aplicación:
   ```bash
   python src/run.py
   ```
3. Accede a la API en `http://localhost:8000`

## Desarrollo

Para contribuir al proyecto:

1. Clona el repositorio
2. Crea un entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Realiza tus cambios
5. Ejecuta las pruebas antes de hacer commit

## API Endpoints

- `GET /`: API status
- `GET /kanji`: Get all kanji cards
- `GET /quiz/kanji-significado`: Get a kanji meaning quiz
- `POST /quiz/kanji-significado/answer`: Submit a quiz answer

## Development

- Utility scripts are in `src/utils/`
- Data files are stored in `data/`
- SRS state is managed in `data/srs_states/` 