import os

# Get the root directory of the project
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Data paths
DATA_DIR = os.path.join(ROOT_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "kanji.db")
KANJI_DATA_PATH = os.path.join(DATA_DIR, "kanji_data.json")
KANJI_MEANINGS_PATH = os.path.join(DATA_DIR, "kanji_meanings_readings.json")
FAILED_KANJI_PATH = os.path.join(DATA_DIR, "failed_kanji.json")

# SRS states paths
SRS_STATES_DIR = os.path.join(DATA_DIR, "srs_states")
SRS_STATE_LECTURA_PATH = os.path.join(SRS_STATES_DIR, "srs_state_lectura.json")
SRS_STATE_SIGNIFICADO_PATH = os.path.join(SRS_STATES_DIR, "srs_state_significado.json") 