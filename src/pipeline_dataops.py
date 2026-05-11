import os
import logging
from google.cloud import bigquery
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Configurar logs para guardar evidencia
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("--- INICIANDO PIPELINE DATAOPS ---")
    load_dotenv()
    
    # 1. INGESTA
    logging.info("Fase 1: Ingesta de datos desde BigQuery...")
    client = bigquery.Client()
    
    # Extraemos un resumen anual para el último año disponible (2016) para mayor velocidad
    query = """
        SELECT 
            borough,
            major_category,
            minor_category,
            year,
            month,
            SUM(value) as total_crimes
        FROM `bigquery-public-data.london_crime.crime_by_lsoa`
        WHERE year = 2016
        GROUP BY 1, 2, 3, 4, 5
    """
    
    try:
        df = client.query(query).to_dataframe()
        logging.info(f"Ingesta completada. Filas extraídas: {len(df)}")
    except Exception as e:
        logging.error(f"Error en la Ingesta: {e}")
        return

    # 2. LIMPIEZA Y TRANSFORMACIÓN
    logging.info("Fase 2: Limpieza y Transformación...")
    try:
        # Tratamiento de nulos
        df = df.dropna(subset=['borough', 'major_category'])
        
        # Agregación: calculamos el total de crímenes por municipio y categoría mayor
        df_agrupado = df.groupby(['borough', 'major_category'], as_index=False)['total_crimes'].sum()
        
        # Renombramos columnas para estandarizar
        df_agrupado = df_agrupado.rename(columns={
            'borough': 'municipio',
            'major_category': 'categoria_delito',
            'total_crimes': 'total_incidentes'
        })
        logging.info(f"Transformación completada. Filas resultantes: {len(df_agrupado)}")
    except Exception as e:
        logging.error(f"Error en la Transformación: {e}")
        return

    # 3. VALIDACIÓN ESTRUCTURAL Y SEMÁNTICA
    logging.info("Fase 3: Validación Estructural y Semántica...")
    try:
        # Validar esquema
        columnas_esperadas = ['municipio', 'categoria_delito', 'total_incidentes']
        assert list(df_agrupado.columns) == columnas_esperadas, "El esquema de columnas no coincide"
        
        # Validar semántica (no debe haber incidentes negativos)
        assert (df_agrupado['total_incidentes'] >= 0).all(), "Existen valores negativos en los incidentes"
        
        # Validar completitud (no nulos)
        assert df_agrupado.isnull().sum().sum() == 0, "Existen valores nulos en el dataset limpio"
        
        logging.info("Validación exitosa. Los datos cumplen las reglas de calidad.")
    except AssertionError as ae:
        logging.error(f"Error de Validación de Calidad: {ae}")
        return
    except Exception as e:
        logging.error(f"Error inesperado en Validación: {e}")
        return

    # 4. CARGA
    logging.info("Fase 4: Carga a Supabase (PostgreSQL)...")
    try:
        db_url = os.getenv("SUPABASE_DB_URL")
        if not db_url:
            raise ValueError("No se encontró SUPABASE_DB_URL en el archivo .env")
        
        # SQLAlchemy necesita 'postgresql://' en lugar de 'postgres://' (ya está correcto en el .env)
        engine = create_engine(db_url)
        
        # Insertar en base de datos. if_exists='replace' sobrescribe la tabla para la demo.
        df_agrupado.to_sql(
            name='london_crime_aggregated', 
            con=engine, 
            if_exists='replace', 
            index=False
        )
        logging.info("Carga completada exitosamente en la tabla 'london_crime_aggregated'.")
    except Exception as e:
        logging.error(f"Error en la Carga de datos: {e}")
        return

    logging.info("--- PIPELINE DATAOPS FINALIZADO CON ÉXITO ---")

if __name__ == "__main__":
    main()
