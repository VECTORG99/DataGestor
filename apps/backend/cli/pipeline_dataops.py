import os
import sys
import argparse
import logging

from dotenv import load_dotenv

if str(settings.PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(settings.PROJECT_ROOT))

from config import settings
from apps.backend.pipeline.ingestion import ingest_data_from_bigquery, get_sample_data
from apps.backend.pipeline.cleaning import (
    clean_and_transform_data,
    validate_data_quality,
)
from apps.backend.pipeline.loading import load_to_supabase, save_clean_data
from apps.backend.pipeline.data_stage_manager import DataStageManager
from apps.backend.pipeline.metrics import MetricsCollector

log_dir = settings.LOG_DIR
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.FileHandler(str(log_dir / settings.LOG_FILENAME)),
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

    load_dotenv(dotenv_path=settings.PROJECT_ROOT / ".env")

    try:
        settings.validate_required_env_vars(demo_mode=args.demo)
    except EnvironmentError as e:
        logging.warning(f"Validación de entorno: {e}")
        if not args.demo:
            logging.warning("El pipeline continuará en modo demo automáticamente.")
            args.demo = True

    logging.info("--- INICIANDO PIPELINE DATAOPS ---")

    metrics = MetricsCollector()

    if not args.demo:
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS_FALLBACK
        if os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)
            logging.info("Credenciales de Google Cloud configuradas")
        else:
            logging.warning("credentials.json no encontrado. Se usará modo demo automáticamente.")
            args.demo = True

    metrics.set_demo_mode(args.demo)

    try:
        stage_manager = DataStageManager(data_root=settings.DATA_DIR)

        metrics.start_stage("ingesta")
        if args.demo:
            logging.info("=" * 70)
            logging.info("FASE 1: INGESTA - MODO DEMO (datos sintéticos)")
            logging.info("=" * 70)
            df = get_sample_data(n_rows=settings.SAMPLE_N_ROWS)
        else:
            df = ingest_data_from_bigquery()
        metrics.end_stage(records_out=len(df))

        initial_count = len(df)

        stage_manager.save_raw_data(df, filename=settings.RAW_FILENAME)

        metrics.start_stage("limpieza", records_in=initial_count)
        df_agrupado = clean_and_transform_data(df)
        metrics.end_stage(records_out=len(df_agrupado))

        metrics.start_stage("validacion")
        validate_data_quality(df_agrupado)
        metrics.end_stage()

        null_count = df_agrupado[["borough", "year", "month", "total_crimes"]].isnull().sum().sum()
        total_cells = len(df_agrupado) * 4
        completeness = (
            ((total_cells - null_count) / total_cells) * 100 if total_cells > 0 else 100.0
        )
        metrics.set_completeness(completeness)

        stage_manager.validate_and_save_validated(
            df_agrupado,
            filename=settings.VALIDATED_FILENAME,
            validation_report_filename=settings.VALIDATION_REPORT_FILENAME,
        )

        metrics.start_stage("guardado")
        output_dir = settings.PROCESSED_DIR
        rutas = save_clean_data(df_agrupado, output_dir)
        metrics.end_stage()
        logging.info(f"Archivos guardados: {rutas}")

        stage_manager.save_processed_data(
            df_agrupado,
            filename=settings.PROCESSED_FILENAME,
            formats=settings.EXPORT_FORMATS,
        )

        metrics.start_stage("carga_supabase")
        try:
            load_to_supabase(df_agrupado)
        except Exception as e:
            logging.warning(f"No se pudo cargar a Supabase: {e}")
            logging.warning("El pipeline continúa. Verifica la configuración en .env")
        metrics.end_stage()

        metrics.set_records(initial_count, len(df_agrupado))
        final_metrics = metrics.finalize()

        metrics_path = metrics.save(settings.METRICS_DIR)
        logging.info(f"KPIs guardados en: {metrics_path}")

        kpi_summary = final_metrics.summary()
        for line in kpi_summary.split("\n"):
            logging.info(line)

        logging.info("--- PIPELINE DATAOPS FINALIZADO CON ÉXITO ---")

    except Exception as e:
        logging.error(f"Pipeline falló: {e}")
        return


if __name__ == "__main__":
    main()
