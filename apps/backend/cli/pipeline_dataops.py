import os
import sys
import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.backend.pipeline.ingestion import ingest_data_from_bigquery, get_sample_data  # noqa: E402
from apps.backend.pipeline.cleaning import (  # noqa: E402
    clean_and_transform_data,
    validate_data_quality,
)
from apps.backend.pipeline.loading import load_to_supabase, save_clean_data  # noqa: E402

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
    parser = argparse.ArgumentParser(description="Pipeline ETL de London Crime DataOps")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Usa datos sintéticos de muestra en lugar de BigQuery",
    )
    args = parser.parse_args()

    logging.info("--- INICIANDO PIPELINE DATAOPS ---")
    load_dotenv(dotenv_path=ROOT_DIR / ".env")

    # Autenticar GCP (solo si no es modo demo)
    if not args.demo:
        credentials_path = ROOT_DIR / "config" / "credentials.json"
        if credentials_path.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)
            logging.info("Credenciales de Google Cloud configuradas")
        else:
            logging.warning("credentials.json no encontrado. Se usará modo demo automáticamente.")
            args.demo = True

    try:
        # 1. INGESTA
        if args.demo:
            logging.info("=" * 70)
            logging.info("FASE 1: INGESTA — MODO DEMO (datos sintéticos)")
            logging.info("=" * 70)
            df = get_sample_data(n_rows=150)
        else:
            df = ingest_data_from_bigquery()

        # 2. LIMPIEZA Y TRANSFORMACIÓN
        df_agrupado = clean_and_transform_data(df)

        # 3. VALIDACIÓN
        validate_data_quality(df_agrupado)

        # 4. GUARDADO LOCAL
        output_dir = ROOT_DIR / "data" / "processed"
        rutas = save_clean_data(df_agrupado, output_dir)
        logging.info(f"Archivos guardados: {rutas}")

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
