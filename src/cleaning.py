"""
Módulo de Limpieza y Transformación de Datos
Responsable de limpiar, transformar y validar la calidad de los datos
"""
import logging
import pandas as pd


def clean_and_transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y transforma los datos extraídos.
    
    Args:
        df (pd.DataFrame): DataFrame con datos sin procesar
        
    Returns:
        pd.DataFrame: DataFrame limpio y transformado
        
    Raises:
        Exception: Si hay error durante la limpieza
    """
    logging.info("Fase 2: Limpieza y Transformación...")
    
    try:
        # Tratamiento de nulos
        df = df.dropna(subset=['borough', 'major_category'])
        
        # Agregación: calculamos el total de crímenes por municipio y categoría mayor
        # La columna 'value' contiene el conteo de incidentes en el dataset de BigQuery
        df_agrupado = df.groupby(['borough', 'major_category'], as_index=False)['value'].sum()
        
        # Renombramos columnas para estandarizar
        df_agrupado = df_agrupado.rename(columns={
            'borough': 'municipio',
            'major_category': 'categoria_delito',
            'value': 'total_incidentes'
        })
        
        logging.info(f"Transformación completada. Filas resultantes: {len(df_agrupado)}")
        return df_agrupado
        
    except Exception as e:
        logging.error(f"Error en la Transformación: {e}")
        raise


def validate_data_quality(df: pd.DataFrame) -> bool:
    """
    Valida la calidad estructural y semántica de los datos.
    
    Args:
        df (pd.DataFrame): DataFrame a validar
        
    Returns:
        bool: True si pasa todas las validaciones
        
    Raises:
        AssertionError: Si alguna validación falla
    """
    logging.info("Fase 3: Validación Estructural y Semántica...")
    
    try:
        # Validar esquema
        columnas_esperadas = ['municipio', 'categoria_delito', 'total_incidentes']
        assert list(df.columns) == columnas_esperadas, "El esquema de columnas no coincide"
        
        # Validar semántica (no debe haber incidentes negativos)
        assert (df['total_incidentes'] >= 0).all(), "Existen valores negativos en los incidentes"
        
        # Validar completitud (no nulos)
        assert df.isnull().sum().sum() == 0, "Existen valores nulos en el dataset limpio"
        
        logging.info("Validación exitosa. Los datos cumplen las reglas de calidad.")
        return True
        
    except AssertionError as ae:
        logging.error(f"Error de Validación de Calidad: {ae}")
        raise
    except Exception as e:
        logging.error(f"Error inesperado en Validación: {e}")
        raise
