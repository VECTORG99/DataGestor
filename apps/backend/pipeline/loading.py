"""
Módulo de Carga de Datos
Responsable de cargar datos procesados en Supabase (PostgreSQL) y guardar a disco.
"""

import os
from pathlib import Path
import logging
from typing import Union, Dict
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()


def save_clean_data(df: pd.DataFrame, output_dir: Union[str, Path]) -> Dict[str, str]:
    """
    Guarda el DataFrame limpio en data/processed/ en formatos CSV y Parquet.

    Args:
        df (pd.DataFrame): DataFrame limpio a persistir.
        output_dir (str | Path): Directorio de salida (data/processed).

    Returns:
        dict[str, str]: Rutas de los archivos generados {'csv': ..., 'parquet': ...}.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "london_crime_aggregated.csv"
    parquet_path = output_dir / "london_crime_aggregated.parquet"

    # Verificar que las columnas esperadas estén presentes
    expected_columns = ["borough", "major_category", "minor_category", "year", "month", "total_crimes", "date"]
    if not all(col in df.columns for col in expected_columns):
        missing = [col for col in expected_columns if col not in df.columns]
        logging.error(f"Columnas faltantes en el DataFrame: {missing}")
        raise ValueError(f"DataFrame no contiene las columnas esperadas: {missing}")

    df.to_csv(csv_path, index=False)
    logging.info("Datos guardados en %s", csv_path)

    df.to_parquet(parquet_path, index=False)
    logging.info("Datos guardados en %s", parquet_path)

    return {"csv": str(csv_path), "parquet": str(parquet_path)}


def load_to_supabase(df: pd.DataFrame) -> bool:
    """
    Carga los datos limpios en la base de datos Supabase (PostgreSQL).

    Args:
        df (pd.DataFrame): DataFrame con los datos a cargar

    Returns:
        bool: True si la carga fue exitosa

    Raises:
        Exception: Si hay error en la conexión o carga a base de datos
    """
    logging.info("=" * 70)
    logging.info("FASE 4: CARGA A SUPABASE (PostgreSQL)")
    logging.info("=" * 70)

    try:
        # Obtener URL de conexión
        db_url = os.getenv("SUPABASE_DB_URL")
        if not db_url:
            logging.warning("No se encontró SUPABASE_DB_URL en el archivo .env")
            logging.warning("La carga a Supabase se ha omitido.")
            logging.info("Para habilitar la carga, configura SUPABASE_DB_URL en tu archivo .env")
            return False

        logging.info(f"Conectando a Supabase...")
        logging.info(f"Base de datos: {db_url.split('@')[-1].split('/')[0]}")

        # Validar estructura de datos
        expected_columns = ["borough", "major_category", "minor_category", "year", "month", "total_crimes", "date"]
        if not all(col in df.columns for col in expected_columns):
            missing = [col for col in expected_columns if col not in df.columns]
            logging.error(f"Columnas faltantes en el DataFrame: {missing}")
            raise ValueError(f"DataFrame no contiene las columnas esperadas: {missing}")

        # Crear engine con SQLAlchemy
        engine = create_engine(db_url, echo=False)
        
        # Probar conexión
        with engine.connect() as connection:
            logging.info("Conexión establecida exitosamente")

        # Insertar en base de datos. if_exists='replace' sobrescribe la tabla.
        logging.info(f"Cargando {len(df)} registros en tabla 'london_crime_aggregated'...")
        df.to_sql(
            name="london_crime_aggregated",
            con=engine,
            if_exists="replace",
            index=False,
            method="multi",  # Método más rápido para inserciones masivas
            chunksize=1000   # Insertar en lotes de 1000 registros
        )

        logging.info("=" * 70)
        logging.info("Carga completada exitosamente en tabla 'london_crime_aggregated'")
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
        logging.error("  4. La tabla 'london_crime_aggregated' no puede ser creada")
        raise
