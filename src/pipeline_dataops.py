import os
import logging
from dotenv import load_dotenv

from ingestion import ingest_data_from_bigquery
from cleaning import clean_and_transform_data, validate_data_quality
from loading import load_to_supabase

# Autenticamos nuestra sesión con la cuenta de Google
# Configura la variable de entorno para credenciales JSON
credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json")
if os.path.exists(credentials_path):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    print("[OK] Credenciales de Google Cloud configuradas")
else:
    print("[WARNING] credentials.json no encontrado en la raíz del proyecto")
    print("   Descarga tus credenciales de Google Cloud Console y colócalo en la raíz")

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
    """
    Orquesta el pipeline de datos ETL:
    1. Ingesta desde BigQuery
    2. Limpieza y transformación
    3. Validación de calidad
    4. Carga en Supabase
    """
    logging.info("--- INICIANDO PIPELINE DATAOPS ---")
    load_dotenv()
    
    try:
        # 1. INGESTA
        df = ingest_data_from_bigquery()
        
        # 2. LIMPIEZA Y TRANSFORMACIÓN
        df_agrupado = clean_and_transform_data(df)
        
        # 3. VALIDACIÓN
        validate_data_quality(df_agrupado)
        
        # 4. CARGA
        load_to_supabase(df_agrupado)
        
        logging.info("--- PIPELINE DATAOPS FINALIZADO CON ÉXITO ---")
        
    except Exception as e:
        logging.error(f"Pipeline falló: {e}")
        return

if __name__ == "__main__":
    main()
