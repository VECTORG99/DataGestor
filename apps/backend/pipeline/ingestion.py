"""
Módulo de Ingesta de Datos
Responsable de extraer datos desde BigQuery
"""

import logging
import os
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account


def ingest_data_from_bigquery() -> pd.DataFrame:
    """
    Extrae datos de crímenes en Londres desde BigQuery.

    Returns:
        pd.DataFrame: DataFrame con los datos extraídos

    Raises:
        Exception: Si hay error en la conexión o consulta a BigQuery
    """
    logging.info("Fase 1: Ingesta de datos desde BigQuery...")

    try:
        # Cargar credenciales desde el archivo JSON de Google Cloud
        credentials_path = os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS", "config/credentials.json"
        )

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Archivo de credenciales no encontrado: {credentials_path}\n"
                "Descarga el archivo JSON desde Google Cloud Console y colócalo en config/."
            )

        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = bigquery.Client(project="london-crime-491323", credentials=credentials)

        logging.info("Autenticado con Google Cloud")

        # Extraemos un resumen anual para el último año disponible (2016) para mayor velocidad
        query = """
            SELECT *
            FROM `bigquery-public-data.london_crime.crime_by_lsoa`
            LIMIT 100000;
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
