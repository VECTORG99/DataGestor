"""
Módulo de Ingesta de Datos
Responsable de extraer datos desde BigQuery
"""
import logging
import pandas as pd
from google.cloud import bigquery


def ingest_data_from_bigquery() -> pd.DataFrame:
    """
    Extrae datos de crímenes en Londres desde BigQuery.
    
    Returns:
        pd.DataFrame: DataFrame con los datos extraídos
        
    Raises:
        Exception: Si hay error en la conexión o consulta a BigQuery
    """
    logging.info("Fase 1: Ingesta de datos desde BigQuery...")
    
    client = bigquery.Client("london-crime-491323")
    
    # Extraemos un resumen anual para el último año disponible (2016) para mayor velocidad
    query = """
        SELECT *
        FROM `bigquery-public-data.london_crime.crime_by_lsoa`
        LIMIT 100;
    """
    
    try:
        df = client.query(query).to_dataframe()
        logging.info(f"Ingesta completada. Filas extraídas: {len(df)}")
        return df
    except Exception as e:
        logging.error(f"Error en la Ingesta: {e}")
        raise
