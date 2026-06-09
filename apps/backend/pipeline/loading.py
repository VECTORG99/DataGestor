import os
from pathlib import Path
import logging
from typing import Union, Dict
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

from config import settings

load_dotenv()


def save_clean_data(df: pd.DataFrame, output_dir: Union[str, Path]) -> Dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / f"{settings.SUPABASE_TABLE_NAME}.csv"
    parquet_path = output_dir / f"{settings.SUPABASE_TABLE_NAME}.parquet"

    if not all(col in df.columns for col in settings.EXPECTED_COLUMNS_PROCESSED):
        missing = [col for col in settings.EXPECTED_COLUMNS_PROCESSED if col not in df.columns]
        logging.error(f"Columnas faltantes en el DataFrame: {missing}")
        raise ValueError(f"DataFrame no contiene las columnas esperadas: {missing}")

    df.to_csv(csv_path, index=False)
    logging.info("Datos guardados en %s", csv_path)

    df.to_parquet(parquet_path, index=False)
    logging.info("Datos guardados en %s", parquet_path)

    return {"csv": str(csv_path), "parquet": str(parquet_path)}


def load_to_supabase(df: pd.DataFrame) -> bool:
    logging.info("=" * 70)
    logging.info("FASE 4: CARGA A SUPABASE (PostgreSQL)")
    logging.info("=" * 70)

    try:
        db_url = os.getenv("SUPABASE_DB_URL")
        if not db_url:
            logging.warning("No se encontró SUPABASE_DB_URL en el archivo .env")
            logging.warning("La carga a Supabase se ha omitido.")
            logging.info("Para habilitar la carga, configura SUPABASE_DB_URL en tu archivo .env")
            return False

        logging.info("Conectando a Supabase...")
        logging.info(f"Base de datos: {db_url.split('@')[-1].split('/')[0]}")

        if not all(col in df.columns for col in settings.EXPECTED_COLUMNS_PROCESSED):
            missing = [col for col in settings.EXPECTED_COLUMNS_PROCESSED if col not in df.columns]
            logging.error(f"Columnas faltantes en el DataFrame: {missing}")
            raise ValueError(f"DataFrame no contiene las columnas esperadas: {missing}")

        engine = create_engine(db_url, echo=settings.DB_ECHO)

        with engine.connect():
            logging.info("Conexión establecida exitosamente")

        table_name = settings.SUPABASE_TABLE_NAME
        logging.info(f"Cargando {len(df)} registros en tabla '{table_name}'...")
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists=settings.DB_IF_EXISTS,
            index=False,
            method="multi",
            chunksize=settings.DB_CHUNKSIZE,
        )

        logging.info("=" * 70)
        logging.info(f"Carga completada exitosamente en tabla '{table_name}'")
        logging.info("Registros cargados: {}".format(len(df)))
        logging.info("=" * 70)
        return True

    except Exception as e:
        logging.error("=" * 70)
        logging.error(f"ERROR en la Carga de datos: {e}")
        logging.error("=" * 70)
        logging.error("Posibles causas:")
        logging.error("  1. SUPABASE_DB_URL no está configurado en .env")
        logging.error("  2. Credenciales de Supabase son inválidas")
        logging.error("  3. No hay conexión a Internet o Supabase está caído")
        logging.error(f"  4. La tabla '{settings.SUPABASE_TABLE_NAME}' no puede ser creada")
        raise
