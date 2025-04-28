# Sistema SRS para Kanji

Este proyecto implementa un sistema de repetición espaciada (SRS) para el estudio de kanjis japoneses, utilizando datos de frecuencia de uso de diferentes fuentes.

## Estructura del Proyecto

```
.
├── data/                  # Datos de kanji y documentos
├── src/                   # Código fuente
│   ├── api/              # API FastAPI
│   ├── processing/       # Procesamiento de datos
│   └── utils/           # Utilidades
├── tests/                # Tests
└── requirements.txt      # Dependencias
```

## Características

- Sistema SRS basado en SuperMemo 2
- Datos de frecuencia de uso de múltiples fuentes (Aozora, News, Wikipedia)
- API REST para acceso a los datos
- Seguimiento de progreso individual por kanji

## Instalación

1. Clonar el repositorio
2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Importar datos a la base de datos:
```bash
python src/processing/import_to_db.py
```

4. Iniciar el servidor API:
```bash
python src/api/srs_kanji.py
```

## Uso

Accede a la API en:
- http://127.0.0.1:8001/docs (documentación interactiva)
- http://127.0.0.1:8001/redoc (documentación alternativa)

## Endpoints Principales

- `GET /kanji/review`: Obtiene kanjis para repasar
- `POST /kanji/review/{char}`: Registra una revisión
- `GET /kanji/stats`: Obtiene estadísticas de progreso
