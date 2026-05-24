"""
Módulo de Limpieza y Transformación de Datos
Responsable de limpiar, transformar y validar la calidad de los datos.
Implementa validaciones exhaustivas para el dataset London Crime.
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime


# Configuración de valores considerados como nulos
NULL_VALUES = {None, '', 'NULL', 'null', 'None', 'Unknown', 'unknown', 'N/A', 'n/a', 'NaN'}


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza los nombres de columnas a minúsculas con guiones bajos.
    
    Args:
        df (pd.DataFrame): DataFrame original
        
    Returns:
        pd.DataFrame: DataFrame con columnas renombradas
    """
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
    logging.info(f"Columnas estandarizadas: {list(df.columns)}")
    return df


def handle_null_values(df: pd.DataFrame, columns_to_check: list = None) -> pd.DataFrame:
    """
    Detecta y maneja valores nulos, vacíos, 'Unknown' y 'N/A'.
    
    Args:
        df (pd.DataFrame): DataFrame a procesar
        columns_to_check (list): Columnas a validar (None = todas)
        
    Returns:
        pd.DataFrame: DataFrame con nulos manejados
    """
    logging.info("Paso 1: Detectando y manejando valores nulos...")
    initial_rows = len(df)
    
    if columns_to_check is None:
        columns_to_check = df.columns.tolist()
    
    # Reportar valores nulos encontrados
    null_report = {}
    for col in columns_to_check:
        if col in df.columns:
            # Detectar valores nulos tradicionales
            null_mask = df[col].isnull()
            # Detectar valores nulos codificados como strings
            if df[col].dtype == 'object':
                null_mask |= df[col].isin(NULL_VALUES)
            null_count = null_mask.sum()
            if null_count > 0:
                null_report[col] = null_count
                logging.info(f"  {col}: {null_count} valores nulos detectados")
    
    # Eliminar filas con nulos en columnas críticas
    critical_columns = ['borough', 'major_category', 'value', 'year', 'month']
    for col in critical_columns:
        if col in df.columns:
            df = df[df[col].notna()]
            if df[col].dtype == 'object':
                df = df[~df[col].isin(NULL_VALUES)]
    
    rows_removed = initial_rows - len(df)
    logging.info(f"  Filas eliminadas por valores nulos: {rows_removed}")
    return df


def validate_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida y convierte los tipos de datos al formato correcto.
    
    Args:
        df (pd.DataFrame): DataFrame a procesar
        
    Returns:
        pd.DataFrame: DataFrame con tipos de datos corregidos
        
    Raises:
        ValueError: Si la conversión de tipos falla
    """
    logging.info("Paso 2: Validando y corrigiendo tipos de datos...")
    
    try:
        # Convertir year a entero
        if 'year' in df.columns:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
            logging.info("  year convertido a Int64")
        
        # Convertir month a entero
        if 'month' in df.columns:
            df['month'] = pd.to_numeric(df['month'], errors='coerce').astype('Int64')
            logging.info("  month convertido a Int64")
        
        # Convertir value a numérico
        if 'value' in df.columns:
            df['value'] = pd.to_numeric(df['value'], errors='coerce').astype('float64')
            logging.info("  value convertido a float64")
        
        # Convertir categorías y boroughs a string
        text_columns = ['borough', 'major_category', 'minor_category']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype('string')
                logging.info(f"  {col} convertido a string")
        
        return df
        
    except Exception as e:
        logging.error(f"Error en conversión de tipos: {e}")
        raise ValueError(f"No se pudieron convertir los tipos de datos: {e}")


def validate_value_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta y elimina registros con valores fuera de rango.
    
    Args:
        df (pd.DataFrame): DataFrame a procesar
        
    Returns:
        pd.DataFrame: DataFrame sin registros fuera de rango
    """
    logging.info("Paso 3: Validando rangos de valores...")
    initial_rows = len(df)
    
    # Validar meses (1-12)
    if 'month' in df.columns:
        invalid_months = ~df['month'].between(1, 12)
        month_invalid = invalid_months.sum()
        if month_invalid > 0:
            logging.warning(f"  {month_invalid} registros con meses inválidos (fuera de 1-12)")
            df = df[~invalid_months]
    
    # Validar años (razonables para London Crime)
    if 'year' in df.columns:
        # Asumiendo que los datos son de 2000 en adelante y no en el futuro
        current_year = datetime.now().year
        invalid_years = ~df['year'].between(2000, current_year)
        year_invalid = invalid_years.sum()
        if year_invalid > 0:
            logging.warning(f"  {year_invalid} registros con años inválidos")
            df = df[~invalid_years]
    
    # Validar valores negativos
    if 'value' in df.columns:
        negative_values = (df['value'] < 0).sum()
        if negative_values > 0:
            logging.warning(f"  {negative_values} registros con valores negativos")
            df = df[df['value'] >= 0]
    
    rows_removed = initial_rows - len(df)
    logging.info(f"  Filas eliminadas por valores fuera de rango: {rows_removed}")
    return df


def normalize_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza nombres de boroughs y categorías:
    - Elimina espacios innecesarios
    - Unifica mayúsculas/minúsculas
    - Corrige errores ortográficos comunes
    
    Args:
        df (pd.DataFrame): DataFrame a procesar
        
    Returns:
        pd.DataFrame: DataFrame con campos normalizados
    """
    logging.info("Paso 4: Normalizando campos de texto...")
    
    text_columns = ['borough', 'major_category', 'minor_category']
    
    for col in text_columns:
        if col in df.columns:
            # Strip espacios y convertir a título case
            df[col] = df[col].str.strip().str.title()
            logging.info(f"  {col} normalizado (espacios eliminados, caso unificado)")
    
    # Diccionario de correcciones ortográficas comunes
    borough_corrections = {
        'City Of London': 'City of London',
        'Kensington And Chelsea': 'Kensington and Chelsea',
        'Hammersmith And Fulham': 'Hammersmith and Fulham',
        'Barking And Dagenham': 'Barking and Dagenham',
    }
    
    if 'borough' in df.columns:
        df['borough'] = df['borough'].replace(borough_corrections)
        logging.info("  Correcciones ortográficas aplicadas a boroughs")
    
    return df


def detect_and_remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta y elimina duplicados considerando:
    - Duplicados completamente idénticos
    - Duplicados por combinación: borough, major_category, year, month
    
    Args:
        df (pd.DataFrame): DataFrame a procesar
        
    Returns:
        pd.DataFrame: DataFrame sin duplicados
    """
    logging.info("Paso 5: Detectando y eliminando duplicados...")
    initial_rows = len(df)
    
    # Detectar duplicados completamente idénticos
    complete_duplicates = df.duplicated().sum()
    if complete_duplicates > 0:
        logging.warning(f"  {complete_duplicates} registros completamente duplicados")
        df = df.drop_duplicates()
    
    # Detectar duplicados por combinación de campos
    if all(col in df.columns for col in ['borough', 'major_category', 'year', 'month']):
        subset_duplicates = df.duplicated(
            subset=['borough', 'major_category', 'year', 'month'],
            keep=False
        ).sum()
        if subset_duplicates > 0:
            logging.warning(
                f"  {subset_duplicates} registros duplicados por "
                f"(borough, major_category, year, month)"
            )
            # Mantener el primer registro de cada grupo
            df = df.drop_duplicates(
                subset=['borough', 'major_category', 'year', 'month'],
                keep='first'
            )
    
    rows_removed = initial_rows - len(df)
    logging.info(f"  Filas eliminadas por duplicados: {rows_removed}")
    return df


def create_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea una columna de fecha unificada en formato datetime.
    
    Args:
        df (pd.DataFrame): DataFrame a procesar
        
    Returns:
        pd.DataFrame: DataFrame con columna de fecha adicional
    """
    logging.info("Paso 6: Creando columna de fecha unificada...")
    
    if 'year' in df.columns and 'month' in df.columns:
        try:
            # Crear fecha asumiendo el primer día del mes
            df['date'] = pd.to_datetime(
                df[['year', 'month']].assign(day=1),
                errors='coerce'
            )
            logging.info("  Columna 'date' creada en formato datetime")
        except Exception as e:
            logging.error(f"Error al crear columna de fecha: {e}")
    
    return df


def detect_outliers(df: pd.DataFrame, method: str = 'iqr') -> dict:
    """
    Detecta valores atípicos (outliers) en la columna 'value'.
    
    Args:
        df (pd.DataFrame): DataFrame a procesar
        method (str): Método de detección ('iqr' o 'zscore')
        
    Returns:
        dict: Información sobre outliers detectados
    """
    logging.info("Paso 7: Detectando valores atípicos (outliers)...")
    
    outliers_info = {
        'method': method,
        'outliers_detected': 0,
        'outlier_indices': [],
        'outlier_values': []
    }
    
    if 'value' not in df.columns:
        logging.warning("  Columna 'value' no encontrada para detección de outliers")
        return outliers_info
    
    if method == 'iqr':
        Q1 = df['value'].quantile(0.25)
        Q3 = df['value'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outlier_mask = (df['value'] < lower_bound) | (df['value'] > upper_bound)
        
    elif method == 'zscore':
        z_scores = np.abs((df['value'] - df['value'].mean()) / df['value'].std())
        outlier_mask = z_scores > 3
    
    else:
        logging.warning(f"Método desconocido: {method}")
        return outliers_info
    
    outlier_indices = df[outlier_mask].index.tolist()
    outlier_values = df[outlier_mask]['value'].tolist()
    
    outliers_info['outliers_detected'] = len(outlier_indices)
    outliers_info['outlier_indices'] = outlier_indices
    outliers_info['outlier_values'] = outlier_values
    
    if len(outlier_indices) > 0:
        logging.info(f"  {len(outlier_indices)} valores atípicos detectados (método: {method})")
        logging.info(f"  Rango típico: {df['value'].quantile(0.05):.0f} - {df['value'].quantile(0.95):.0f}")
        logging.info(f"  Valores atípicos: min={min(outlier_values):.0f}, max={max(outlier_values):.0f}")
    else:
        logging.info("  No se detectaron valores atípicos")
    
    return outliers_info


def remove_unnecessary_columns(df: pd.DataFrame, keep_columns: list = None) -> pd.DataFrame:
    """
    Elimina columnas innecesarias o redundantes.
    
    Args:
        df (pd.DataFrame): DataFrame a procesar
        keep_columns (list): Columnas que deben mantenerse (None = automático)
        
    Returns:
        pd.DataFrame: DataFrame con columnas optimizadas
    """
    logging.info("Paso 8: Eliminando columnas innecesarias...")
    
    if keep_columns is None:
        keep_columns = ['borough', 'major_category', 'minor_category', 'year', 'month', 'value', 'date']
    
    columns_to_drop = [col for col in df.columns if col not in keep_columns]
    
    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)
        logging.info(f"  Columnas eliminadas: {columns_to_drop}")
    
    return df


def clean_and_transform_data(df: pd.DataFrame, remove_outliers: bool = False) -> pd.DataFrame:
    """
    Orquesta todo el proceso de limpieza y transformación del dataset.
    
    Args:
        df (pd.DataFrame): DataFrame con datos sin procesar
        remove_outliers (bool): Si True, elimina los outliers detectados
        
    Returns:
        pd.DataFrame: DataFrame limpio y transformado
        
    Raises:
        Exception: Si hay error durante la limpieza
    """
    logging.info("=" * 70)
    logging.info("FASE 2: LIMPIEZA Y TRANSFORMACIÓN DE DATOS")
    logging.info("=" * 70)
    logging.info(f"Registros iniciales: {len(df)}")
    
    try:
        # 1. Estandarizar nombres de columnas
        df = standardize_column_names(df)
        
        # 2. Manejo de valores nulos
        df = handle_null_values(df)
        
        # 3. Validación de tipos de datos
        df = validate_data_types(df)
        
        # 4. Validación de rangos
        df = validate_value_ranges(df)
        
        # 5. Normalización de texto
        df = normalize_text_fields(df)
        
        # 6. Eliminación de duplicados
        df = detect_and_remove_duplicates(df)
        
        # 7. Crear columna de fecha
        df = create_date_column(df)
        
        # 8. Detectar outliers
        outliers_info = detect_outliers(df, method='iqr')
        if remove_outliers and outliers_info['outliers_detected'] > 0:
            df = df.drop(outliers_info['outlier_indices'])
            logging.info(f"  Outliers eliminados: {outliers_info['outliers_detected']}")
        
        # 9. Eliminar columnas innecesarias
        df = remove_unnecessary_columns(df)
        
        logging.info("=" * 70)
        logging.info(f"Registros finales: {len(df)}")
        logging.info("Transformación completada exitosamente")
        logging.info("=" * 70)
        
        return df
        
    except Exception as e:
        logging.error(f"Error en la Transformación: {e}")
        raise


def validate_data_quality(df: pd.DataFrame) -> bool:
    """
    Valida la calidad estructural y semántica de los datos después de la limpieza.
    
    Args:
        df (pd.DataFrame): DataFrame a validar
        
    Returns:
        bool: True si pasa todas las validaciones
        
    Raises:
        AssertionError: Si alguna validación falla
    """
    logging.info("=" * 70)
    logging.info("FASE 3: VALIDACIÓN ESTRUCTURAL Y SEMÁNTICA")
    logging.info("=" * 70)
    
    try:
        # Validar esquema
        columnas_esperadas = {'borough', 'major_category', 'minor_category', 'year', 'month', 'value', 'date'}
        columnas_presentes = set(df.columns)
        assert columnas_esperadas.issubset(columnas_presentes), \
            f"Columnas faltantes: {columnas_esperadas - columnas_presentes}"
        logging.info("Esquema de columnas validado")
        
        # Validar tipos de datos
        assert df['year'].dtype in ['int64', 'Int64'], "year debe ser entero"
        assert df['month'].dtype in ['int64', 'Int64'], "month debe ser entero"
        assert df['value'].dtype in ['float64', 'int64', 'Int64'], "value debe ser numérico"
        logging.info("Tipos de datos validados")
        
        # Validar completitud (no nulos)
        null_count = df[['borough', 'major_category', 'year', 'month', 'value']].isnull().sum().sum()
        assert null_count == 0, f"Existen {null_count} valores nulos en el dataset limpio"
        logging.info("Sin valores nulos en columnas críticas")
        
        # Validar semántica
        assert (df['year'] >= 2000).all(), "Años menores a 2000 detectados"
        assert (df['month'].between(1, 12)).all(), "Meses fuera del rango 1-12 detectados"
        assert (df['value'] >= 0).all(), "Valores negativos en incidentes detectados"
        logging.info("Rangos de valores validados")
        
        # Validar sin duplicados
        duplicates = df.duplicated(subset=['borough', 'major_category', 'year', 'month']).sum()
        assert duplicates == 0, f"Se encontraron {duplicates} registros duplicados"
        logging.info("Sin registros duplicados")
        
        # Validar formato de fechas
        assert df['date'].dtype == 'datetime64[ns]', "date debe estar en formato datetime"
        logging.info("Formato de fechas validado")
        
        logging.info("=" * 70)
        logging.info("VALIDACIÓN EXITOSA: Los datos cumplen todas las reglas de calidad")
        logging.info("=" * 70)
        return True
        
    except AssertionError as ae:
        logging.error(f"✗ Error de Validación de Calidad: {ae}")
        raise
    except Exception as e:
        logging.error(f"✗ Error inesperado en Validación: {e}")
        raise
