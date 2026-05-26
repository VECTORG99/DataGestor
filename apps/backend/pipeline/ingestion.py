"""
Módulo de Ingesta de Datos
Responsable de extraer datos desde BigQuery o generar datos de muestra.
"""

import logging
import os
import pandas as pd
import numpy as np


SAMPLE_BOROUGHS = [
    "City of London",
    "Westminster",
    "Camden",
    "Islington",
    "Hackney",
    "Tower Hamlets",
    "Greenwich",
    "Lewisham",
    "Southwark",
    "Lambeth",
    "Wandsworth",
    "Hammersmith and Fulham",
    "Kensington and Chelsea",
    "Brent",
    "Ealing",
    "Hounslow",
    "Richmond upon Thames",
    "Kingston upon Thames",
    "Merton",
    "Sutton",
    "Croydon",
    "Bromley",
    "Bexley",
    "Havering",
    "Barking and Dagenham",
    "Redbridge",
    "Newham",
    "Waltham Forest",
    "Haringey",
    "Enfield",
    "Barnet",
    "Harrow",
    "Hillingdon",
]

MAJOR_CATEGORIES = {
    "Burglary": ["Burglary in a dwelling", "Burglary in other buildings"],
    "Criminal Damage": ["Criminal damage to a vehicle", "Other criminal damage"],
    "Drugs": ["Possession of cannabis", "Possession of class A drugs", "Other drug offences"],
    "Robbery": ["Robbery of business property", "Robbery of personal property"],
    "Sexual Offences": ["Rape", "Sexual assault", "Other sexual offences"],
    "Theft and Handling": [
        "Pickpocketing",
        "Shoplifting",
        "Theft from a vehicle",
        "Theft of a vehicle",
        "Other theft",
    ],
    "Violence Against the Person": [
        "Assault with injury",
        "Assault without injury",
        "Harassment",
        "Murder",
    ],
    "Fraud or Forgery": ["Fraud", "Forgery or use of false instrument"],
    "Other Notifiable Offences": ["Other notifiable offences"],
}


def get_sample_data(n_rows: int = 150) -> pd.DataFrame:
    """
    Genera un DataFrame sintético que replica la estructura del dataset
    `bigquery-public-data.london_crime.crime_by_lsoa`.

    Args:
        n_rows (int): Número aproximado de registros a generar.

    Returns:
        pd.DataFrame: Datos sintéticos listos para el pipeline de limpieza.
    """
    np.random.seed(42)
    records = []
    lsoa_pool = [f"E010{n:05d}" for n in range(1, 200)]

    for _ in range(n_rows):
        borough = np.random.choice(SAMPLE_BOROUGHS)
        major = np.random.choice(list(MAJOR_CATEGORIES.keys()))
        minor = np.random.choice(MAJOR_CATEGORIES[major])
        records.append(
            {
                "lsoa_code": np.random.choice(lsoa_pool),
                "borough": borough,
                "major_category": major,
                "minor_category": minor,
                "value": int(np.random.poisson(15)),
                "year": int(np.random.choice([2016, 2017, 2018, 2019])),
                "month": int(np.random.randint(1, 13)),
            }
        )

    df = pd.DataFrame(records)

    # Inyectar algunos valores problemáticos para ejercitar la limpieza
    # (None en borough, mes inválido, valor negativo, "Unknown")
    df.loc[0, "borough"] = None
    df.loc[1, "month"] = 13
    df.loc[2, "value"] = -5
    df.loc[3, "minor_category"] = "Unknown"

    logging.info(
        f"   Muestra sintética generada: {len(df)} registros, {df['borough'].nunique()} distritos"
    )
    return df


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
        from google.cloud import bigquery
        from google.oauth2 import service_account

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
