import os
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.backend.pipeline.ingestion import ingest_data_from_bigquery  # noqa: E402
from apps.backend.pipeline.cleaning import (  # noqa: E402
    clean_and_transform_data,
    validate_data_quality,
)
from apps.backend.pipeline.loading import load_to_supabase, save_clean_data  # noqa: E402

# Autenticamos nuestra sesión con la cuenta de Google
# Configura la variable de entorno para credenciales JSON
credentials_path = ROOT_DIR / "config" / "credentials.json"
if credentials_path.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)
    print("Credenciales de Google Cloud configuradas")
else:
    print("[WARNING] credentials.json no encontrado en config/")
    print("   Descarga tus credenciales de Google Cloud Console y colócalo en config/")

# Configurar logs para guardar evidencia
log_dir = ROOT_DIR / "data" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(log_dir / "pipeline.log")),
        logging.StreamHandler(),
    ],
)


def main():
    """
    Orquesta el pipeline de datos ETL:
    1. Ingesta desde BigQuery
    2. Limpieza y transformación
    3. Validación de calidad
    4. Guardado local en data/processed/
    5. Carga en Supabase (opcional)
    """
    logging.info("--- INICIANDO PIPELINE DATAOPS ---")
    load_dotenv(dotenv_path=ROOT_DIR / ".env")

    try:
        # 1. INGESTA
        df = ingest_data_from_bigquery()

        # 2. LIMPIEZA Y TRANSFORMACIÓN
        df_agrupado = clean_and_transform_data(df)

        # 3. VALIDACIÓN
        validate_data_quality(df_agrupado)

        # 4. GUARDADO LOCAL
        output_dir = ROOT_DIR / "data" / "processed"
        save_clean_data(df_agrupado, output_dir)

        # 5. CARGA A SUPABASE (opcional - si SUPABASE_DB_URL está configurado)
        try:
            load_to_supabase(df_agrupado)
        except Exception as e:
            logging.warning(f"No se pudo cargar a Supabase: {e}")
            logging.warning("El pipeline continúa. Verifica la configuración en .env")

        logging.info("--- PIPELINE DATAOPS FINALIZADO CON ÉXITO ---")

    except Exception as e:
        logging.error(f"Pipeline falló: {e}")
        return


if __name__ == "__main__":
    main()
