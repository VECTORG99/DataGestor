"""
Módulo de Carga de Datos
Responsable de cargar datos procesados en Supabase (PostgreSQL)
"""
import os
import logging
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()


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
    logging.info("Fase 4: Carga a Supabase (PostgreSQL)...")
    
    try:
        db_url = os.getenv("SUPABASE_DB_URL")
        if not db_url:
            raise ValueError("No se encontró SUPABASE_DB_URL en el archivo .env")
        
        # SQLAlchemy necesita 'postgresql://' en lugar de 'postgres://' (ya está correcto en el .env)
        engine = create_engine(db_url)
        
        # Insertar en base de datos. if_exists='replace' sobrescribe la tabla para la demo.
        df.to_sql(
            name='london_crime_aggregated', 
            con=engine, 
            if_exists='replace', 
            index=False
        )
        
        logging.info("Carga completada exitosamente en la tabla 'london_crime_aggregated'.")
        return True
        
    except Exception as e:
        logging.error(f"Error en la Carga de datos: {e}")
        raise
