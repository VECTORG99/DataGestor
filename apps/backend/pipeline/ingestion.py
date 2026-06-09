import logging
import os
import pandas as pd
import numpy as np

from config import settings


def get_sample_data(n_rows: int = None, inject_errors: bool = True) -> pd.DataFrame:
    if n_rows is None:
        n_rows = settings.SAMPLE_N_ROWS

    boroughs = settings.get_sample_boroughs()
    categories = settings.get_sample_categories()

    np.random.seed(settings.SAMPLE_RANDOM_SEED)
    records = []
    lsoa_pool = [
        f"E010{n:05d}" for n in range(settings.SAMPLE_LSOA_RANGE[0], settings.SAMPLE_LSOA_RANGE[1])
    ]

    for _ in range(n_rows):
        borough = np.random.choice(boroughs)
        major = np.random.choice(list(categories.keys()))
        minor = np.random.choice(categories[major])
        records.append(
            {
                "lsoa_code": np.random.choice(lsoa_pool),
                "borough": borough,
                "major_category": major,
                "minor_category": minor,
                "value": int(np.random.poisson(settings.SAMPLE_POISSON_MEAN)),
                "year": int(np.random.choice(settings.SAMPLE_YEARS)),
                "month": int(np.random.randint(
                    settings.VALIDATION_MONTH_MIN, settings.VALIDATION_MONTH_MAX + 1
                )),
            }
        )

    df = pd.DataFrame(records)

    if inject_errors:
        df.loc[0, "borough"] = None
        df.loc[1, "month"] = settings.VALIDATION_MONTH_MAX + 1
        df.loc[2, "value"] = -5
        df.loc[3, "minor_category"] = "Unknown"

    logging.info(
        f"   Muestra sintética generada: {len(df)} registros, {df['borough'].nunique()} distritos"
    )
    return df


def ingest_data_from_bigquery() -> pd.DataFrame:
    logging.info("Fase 1: Ingesta de datos desde BigQuery...")

    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account

        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS_FALLBACK

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Archivo de credenciales no encontrado: {credentials_path}\n"
                "Descarga el archivo JSON desde Google Cloud Console y colócalo en config/."
            )

        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = bigquery.Client(
            project=settings.GCP_PROJECT_ID, credentials=credentials
        )

        logging.info("Autenticado con Google Cloud")

        query = f"""
            SELECT *
            FROM `{settings.BIGQUERY_TABLE}`
            LIMIT {settings.BIGQUERY_ROW_LIMIT};
        """

        df = client.query(query).to_dataframe()
        logging.info(f"Ingesta completada. Filas extraídas: {len(df)}")
        return df

    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
        raise
    except Exception as e:
        logging.error(f"Error en la Ingesta: {e}")
        raise
