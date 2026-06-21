import json
import os
from pathlib import Path
from typing import Dict, List, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Directorios
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))
RAW_DIR = Path(os.getenv("RAW_DIR", DATA_DIR / "raw"))
VALIDATED_DIR = Path(os.getenv("VALIDATED_DIR", DATA_DIR / "validated"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", DATA_DIR / "processed"))
LOG_DIR = Path(os.getenv("LOG_DIR", DATA_DIR / "logs"))
METRICS_DIR = Path(os.getenv("METRICS_DIR", DATA_DIR / "metrics"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s [%(levelname)s] %(message)s")
LOG_FILENAME = os.getenv("LOG_FILENAME", "pipeline.log")

# ---------------------------------------------------------------------------
# GCP / BigQuery
# ---------------------------------------------------------------------------
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "london-crime-491323")
BIGQUERY_TABLE = os.getenv(
    "BIGQUERY_TABLE", "bigquery-public-data.london_crime.crime_by_lsoa"
)
# Limite de filas a extraer de BigQuery.
#   - 1_000_000 raw (~295 MB parquet) → ~44_886 agregadas (~3 MB CSV)
#   - Supabase Free Tier: 500 MB total DB
#   - Ajustar segun margen disponible. Ej: 2_000_000 ocupa ~6 MB (~1.2% del limite)
BIGQUERY_ROW_LIMIT = int(os.getenv("BIGQUERY_ROW_LIMIT", "1000000"))
GOOGLE_APPLICATION_CREDENTIALS_FALLBACK = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS_FALLBACK",
    str(PROJECT_ROOT / "config" / "credentials.json"),
)

# ---------------------------------------------------------------------------
# Supabase / Database
#   Free Tier limits: 500 MB DB, 2 GB bandwidth, 5 GB row limit
#   ~44k filas agregadas ≈ 8 MB → ~1.6% del limite de 500 MB
#   A 237 bytes/fila, 500 MB darian para ~2.1M filas agregadas
# ---------------------------------------------------------------------------
SUPABASE_TABLE_NAME = os.getenv("SUPABASE_TABLE_NAME", "london_crime_aggregated")
DB_IF_EXISTS = os.getenv("DB_IF_EXISTS", "replace")
DB_CHUNKSIZE = int(os.getenv("DB_CHUNKSIZE", "1000"))
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
EXPORT_COMPRESSION = os.getenv("EXPORT_COMPRESSION", "snappy")
EXPORT_FORMATS: List[str] = os.getenv("EXPORT_FORMATS", "parquet,csv").split(",")

# ---------------------------------------------------------------------------
# Validación de rangos
# ---------------------------------------------------------------------------
VALIDATION_MIN_YEAR = int(os.getenv("VALIDATION_MIN_YEAR", "2000"))
VALIDATION_MONTH_MIN = int(os.getenv("VALIDATION_MONTH_MIN", "1"))
VALIDATION_MONTH_MAX = int(os.getenv("VALIDATION_MONTH_MAX", "12"))
VALIDATION_IQR_MULTIPLIER = float(os.getenv("VALIDATION_IQR_MULTIPLIER", "1.5"))
VALIDATION_ZSCORE_THRESHOLD = float(os.getenv("VALIDATION_ZSCORE_THRESHOLD", "3"))
VALIDATION_IQR_Q1 = float(os.getenv("VALIDATION_IQR_Q1", "0.25"))
VALIDATION_IQR_Q3 = float(os.getenv("VALIDATION_IQR_Q3", "0.75"))
VALIDATION_REPORT_Q05 = float(os.getenv("VALIDATION_REPORT_Q05", "0.05"))
VALIDATION_REPORT_Q95 = float(os.getenv("VALIDATION_REPORT_Q95", "0.95"))
OUTLIER_DEFAULT_METHOD = os.getenv("OUTLIER_DEFAULT_METHOD", "iqr")

# ---------------------------------------------------------------------------
# Nombres de columnas (no configurables por env, pero centralizados)
# ---------------------------------------------------------------------------
CRITICAL_COLUMNS = ["borough", "major_category", "value", "year", "month"]
TEXT_COLUMNS = ["borough", "major_category", "minor_category"]
GROUPBY_COLS = [
    "borough", "major_category", "minor_category", "year", "month",
]
KEEP_COLUMNS = [
    "borough", "major_category", "minor_category",
    "year", "month", "total_crimes", "date",
]
EXPECTED_COLUMNS_RAW = [
    "borough", "major_category", "minor_category", "year", "month", "value",
]
EXPECTED_COLUMNS_PROCESSED = [
    "borough", "major_category", "minor_category",
    "year", "month", "total_crimes", "date",
]

# ---------------------------------------------------------------------------
# Transformaciones
# ---------------------------------------------------------------------------
COLUMN_RENAME_MAP = {"value": "total_crimes"}
DATE_DAY_DEFAULT = 1
SEPARATOR_LENGTH = 70

# ---------------------------------------------------------------------------
# NULL values
# ---------------------------------------------------------------------------
NULL_VALUES = frozenset({
    "", "NULL", "null", "None", "Unknown", "unknown", "N/A", "n/a", "NaN",
})

# ---------------------------------------------------------------------------
# Borough corrections
# ---------------------------------------------------------------------------
BOROUGH_CORRECTIONS = {
    "City Of London": "City of London",
    "Kensington And Chelsea": "Kensington and Chelsea",
    "Hammersmith And Fulham": "Hammersmith and Fulham",
    "Barking And Dagenham": "Barking and Dagenham",
}

# ---------------------------------------------------------------------------
# Sample data defaults
# ---------------------------------------------------------------------------
SAMPLE_N_ROWS = int(os.getenv("SAMPLE_N_ROWS", "150"))
SAMPLE_RANDOM_SEED = int(os.getenv("SAMPLE_RANDOM_SEED", "42"))
SAMPLE_POISSON_MEAN = int(os.getenv("SAMPLE_POISSON_MEAN", "15"))
SAMPLE_YEARS = [2016, 2017, 2018, 2019]
SAMPLE_LSOA_RANGE = (1, 200)

# ---------------------------------------------------------------------------
# Sample data (cargado desde JSON)
# ---------------------------------------------------------------------------
SAMPLE_BOROUGHS_PATH = PROJECT_ROOT / "config" / "boroughs.json"
SAMPLE_CATEGORIES_PATH = PROJECT_ROOT / "config" / "categories.json"


def _load_json(path: Path) -> Union[list, dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_sample_boroughs() -> list:
    return _load_json(SAMPLE_BOROUGHS_PATH)


def get_sample_categories() -> Dict[str, list]:
    return _load_json(SAMPLE_CATEGORIES_PATH)


# ---------------------------------------------------------------------------
# Nombres de archivos del pipeline
# ---------------------------------------------------------------------------
RAW_FILENAME = os.getenv("RAW_FILENAME", "london_crime_raw")
VALIDATED_FILENAME = os.getenv("VALIDATED_FILENAME", "london_crime_validated")
PROCESSED_FILENAME = os.getenv("PROCESSED_FILENAME", "london_crime_processed")
VALIDATION_REPORT_FILENAME = os.getenv("VALIDATION_REPORT_FILENAME", "validation_report")

# ---------------------------------------------------------------------------
# Variables de entorno requeridas
# ---------------------------------------------------------------------------
REQUIRED_ENV_VARS_PRODUCTION = ["SUPABASE_DB_URL"]
REQUIRED_ENV_VARS_DEMO: List[str] = []


def validate_required_env_vars(demo_mode: bool = False) -> None:
    required = REQUIRED_ENV_VARS_DEMO if demo_mode else REQUIRED_ENV_VARS_PRODUCTION
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise EnvironmentError(
            "Faltan variables de entorno requeridas:\n  "
            + "\n  ".join(missing)
            + "\n\nConfigúralas en tu archivo .env o pásalas como variable de entorno."
        )
