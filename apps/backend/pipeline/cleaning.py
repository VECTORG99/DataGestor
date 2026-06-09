import logging
import pandas as pd
import numpy as np
from datetime import datetime

from config import settings

_SEP = "=" * settings.SEPARATOR_LENGTH


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.lower().str.replace(" ", "_").str.replace("-", "_")
    logging.info(f"Columnas estandarizadas: {list(df.columns)}")
    return df


def handle_null_values(df: pd.DataFrame, columns_to_check: list = None) -> pd.DataFrame:
    logging.info("Paso 1: Detectando y manejando valores nulos...")
    initial_rows = len(df)

    if columns_to_check is None:
        columns_to_check = df.columns.tolist()

    null_report = {}
    for col in columns_to_check:
        if col in df.columns:
            null_mask = df[col].isnull()
            if df[col].dtype in ("object", "string"):
                null_mask |= df[col].isin(settings.NULL_VALUES)
            null_count = null_mask.sum()
            if null_count > 0:
                null_report[col] = null_count
                logging.info(f"  {col}: {null_count} valores nulos detectados")

    for col in settings.CRITICAL_COLUMNS:
        if col in df.columns:
            df = df[df[col].notna()]
            if df[col].dtype in ("object", "string"):
                df = df[~df[col].isin(settings.NULL_VALUES)]

    rows_removed = initial_rows - len(df)
    logging.info(f"  Filas eliminadas por valores nulos: {rows_removed}")
    return df


def validate_data_types(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Paso 2: Validando y corrigiendo tipos de datos...")

    try:
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
            logging.info("  year convertido a Int64")

        if "month" in df.columns:
            df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
            logging.info("  month convertido a Int64")

        if "value" in df.columns:
            df["value"] = pd.to_numeric(df["value"], errors="coerce").astype("float64")
            logging.info("  value convertido a float64")

        for col in settings.TEXT_COLUMNS:
            if col in df.columns:
                df[col] = df[col].astype("string")
                logging.info(f"  {col} convertido a string")

        return df

    except Exception as e:
        logging.error(f"Error en conversión de tipos: {e}")
        raise ValueError(f"No se pudieron convertir los tipos de datos: {e}")


def validate_value_ranges(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Paso 3: Validando rangos de valores...")
    initial_rows = len(df)

    if "month" in df.columns:
        invalid_months = ~df["month"].between(
            settings.VALIDATION_MONTH_MIN, settings.VALIDATION_MONTH_MAX
        )
        month_invalid = invalid_months.sum()
        if month_invalid > 0:
            logging.warning(
                f"  {month_invalid} registros con meses inválidos "
                f"(fuera de {settings.VALIDATION_MONTH_MIN}-{settings.VALIDATION_MONTH_MAX})"
            )
            df = df[~invalid_months]

    if "year" in df.columns:
        current_year = datetime.now().year
        invalid_years = ~df["year"].between(settings.VALIDATION_MIN_YEAR, current_year)
        year_invalid = invalid_years.sum()
        if year_invalid > 0:
            logging.warning(f"  {year_invalid} registros con años inválidos")
            df = df[~invalid_years]

    if "value" in df.columns:
        negative_values = (df["value"] < 0).sum()
        if negative_values > 0:
            logging.warning(f"  {negative_values} registros con valores negativos")
            df = df[df["value"] >= 0]

    rows_removed = initial_rows - len(df)
    logging.info(f"  Filas eliminadas por valores fuera de rango: {rows_removed}")
    return df


def normalize_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Paso 4: Normalizando campos de texto...")

    for col in settings.TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].str.strip().str.title()
            logging.info(f"  {col} normalizado (espacios eliminados, caso unificado)")

    if "borough" in df.columns:
        df["borough"] = df["borough"].replace(settings.BOROUGH_CORRECTIONS)
        logging.info("  Correcciones ortográficas aplicadas a boroughs")

    return df


def detect_and_remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Paso 5: Detectando y eliminando duplicados completamente idénticos...")
    initial_rows = len(df)

    complete_duplicates = df.duplicated().sum()
    if complete_duplicates > 0:
        logging.warning(f"  {complete_duplicates} registros completamente duplicados")
        df = df.drop_duplicates()

    rows_removed = initial_rows - len(df)
    logging.info(f"  Filas eliminadas por duplicados: {rows_removed}")
    return df


def aggregate_crime_data(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Paso 6: Agregando crímenes por ubicación, tipo y período...")
    initial_rows = len(df)

    if all(col in df.columns for col in settings.GROUPBY_COLS):
        df_aggregated = df.groupby(settings.GROUPBY_COLS, as_index=False).agg({"value": "sum"})
        df_aggregated = df_aggregated.rename(columns=settings.COLUMN_RENAME_MAP)

        rows_aggregated = initial_rows - len(df_aggregated)
        if rows_aggregated > 0:
            logging.info(f"  {rows_aggregated} registros agregados (sumados en grupos)")
            logging.info(
                f"  Total de grupos únicos (borough, category, year, month): {len(df_aggregated)}"
            )
        else:
            logging.info("  No había registros duplicados para agregar")

        return df_aggregated
    else:
        logging.warning("  Columnas requeridas para agregación no encontradas")
        return df


def create_date_column(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Paso 7: Creando columna de fecha unificada...")

    if "year" in df.columns and "month" in df.columns:
        try:
            df["date"] = pd.to_datetime(
                df[["year", "month"]].assign(day=settings.DATE_DAY_DEFAULT), errors="coerce"
            )
            logging.info("  Columna 'date' creada en formato datetime")
        except Exception as e:
            logging.error(f"Error al crear columna de fecha: {e}")

    return df


def detect_outliers(df: pd.DataFrame, method: str = None) -> dict:
    if method is None:
        method = settings.OUTLIER_DEFAULT_METHOD
    logging.info("Paso 8: Detectando valores atípicos (outliers)...")

    outliers_info = {
        "method": method,
        "outliers_detected": 0,
        "outlier_indices": [],
        "outlier_values": [],
    }

    if "total_crimes" not in df.columns:
        logging.warning("  Columna 'total_crimes' no encontrada para detección de outliers")
        return outliers_info

    if method == "iqr":
        Q1 = df["total_crimes"].quantile(settings.VALIDATION_IQR_Q1)
        Q3 = df["total_crimes"].quantile(settings.VALIDATION_IQR_Q3)
        IQR = Q3 - Q1
        lower_bound = Q1 - settings.VALIDATION_IQR_MULTIPLIER * IQR
        upper_bound = Q3 + settings.VALIDATION_IQR_MULTIPLIER * IQR

        outlier_mask = (df["total_crimes"] < lower_bound) | (df["total_crimes"] > upper_bound)

    elif method == "zscore":
        z_scores = np.abs(
            (df["total_crimes"] - df["total_crimes"].mean()) / df["total_crimes"].std()
        )
        outlier_mask = z_scores > settings.VALIDATION_ZSCORE_THRESHOLD

    else:
        logging.warning(f"Método desconocido: {method}")
        return outliers_info

    outlier_indices = df[outlier_mask].index.tolist()
    outlier_values = df[outlier_mask]["total_crimes"].tolist()

    outliers_info["outliers_detected"] = len(outlier_indices)
    outliers_info["outlier_indices"] = outlier_indices
    outliers_info["outlier_values"] = outlier_values

    if len(outlier_indices) > 0:
        logging.info(f"  {len(outlier_indices)} valores atípicos detectados (método: {method})")
        q05 = df["total_crimes"].quantile(settings.VALIDATION_REPORT_Q05)
        q95 = df["total_crimes"].quantile(settings.VALIDATION_REPORT_Q95)
        logging.info(f"  Rango típico: {q05:.0f} - {q95:.0f}")
        logging.info(
            f"  Valores atípicos: min={min(outlier_values):.0f}, max={max(outlier_values):.0f}"
        )
    else:
        logging.info("  No se detectaron valores atípicos")

    return outliers_info


def remove_unnecessary_columns(df: pd.DataFrame, keep_columns: list = None) -> pd.DataFrame:
    logging.info("Paso 9: Eliminando columnas innecesarias...")

    if keep_columns is None:
        keep_columns = settings.KEEP_COLUMNS

    columns_to_drop = [col for col in df.columns if col not in keep_columns]

    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)
        logging.info(f"  Columnas eliminadas: {columns_to_drop}")

    return df


def clean_and_transform_data(df: pd.DataFrame) -> pd.DataFrame:
    logging.info(_SEP)
    logging.info("FASE 2: LIMPIEZA Y TRANSFORMACIÓN DE DATOS")
    logging.info(_SEP)
    logging.info(f"Registros iniciales: {len(df)}")

    try:
        df = standardize_column_names(df)
        df = handle_null_values(df)
        df = validate_data_types(df)
        df = validate_value_ranges(df)
        df = normalize_text_fields(df)
        df = detect_and_remove_duplicates(df)
        df = aggregate_crime_data(df)
        df = create_date_column(df)
        detect_outliers(df, method="iqr")
        df = remove_unnecessary_columns(df)

        logging.info(_SEP)
        logging.info(f"Registros finales: {len(df)}")
        logging.info("Transformación completada exitosamente")
        logging.info(_SEP)

        return df

    except Exception as e:
        logging.error(f"Error en la Transformación: {e}")
        raise


def validate_data_quality(df: pd.DataFrame) -> bool:
    logging.info(_SEP)
    logging.info("FASE 3: VALIDACIÓN ESTRUCTURAL Y SEMÁNTICA")
    logging.info(_SEP)

    try:
        columnas_esperadas = set(settings.EXPECTED_COLUMNS_PROCESSED)
        columnas_presentes = set(df.columns)
        assert columnas_esperadas.issubset(
            columnas_presentes
        ), f"Columnas faltantes: {columnas_esperadas - columnas_presentes}"
        logging.info("Esquema de columnas validado")

        assert df["year"].dtype in ["int64", "Int64"], "year debe ser entero"
        assert df["month"].dtype in ["int64", "Int64"], "month debe ser entero"
        assert df["total_crimes"].dtype in [
            "float64",
            "int64",
            "Int64",
        ], "total_crimes debe ser numérico"
        logging.info("Tipos de datos validados")

        null_count = df[["borough", "year", "month", "total_crimes"]].isnull().sum().sum()
        assert null_count == 0, f"Existen {null_count} valores nulos en el dataset limpio"
        logging.info("Sin valores nulos en columnas críticas")

        assert (df["year"] >= settings.VALIDATION_MIN_YEAR).all(), \
            f"Años menores a {settings.VALIDATION_MIN_YEAR} detectados"
        assert (df["month"].between(
            settings.VALIDATION_MONTH_MIN, settings.VALIDATION_MONTH_MAX
        )).all(), "Meses fuera del rango válido detectados"
        assert (df["total_crimes"] >= 0).all(), "Valores negativos en incidentes detectados"
        logging.info("Rangos de valores validados")

        duplicates = df.duplicated(
            subset=settings.GROUPBY_COLS
        ).sum()
        assert duplicates == 0, f"Se encontraron {duplicates} registros duplicados"
        logging.info("Sin registros duplicados")

        assert df["date"].dtype in ("datetime64[ns]", "datetime64[us]"), \
            "date debe estar en formato datetime"
        logging.info("Formato de fechas validado")

        logging.info(_SEP)
        logging.info("VALIDACIÓN EXITOSA: Los datos cumplen todas las reglas de calidad")
        logging.info(_SEP)
        return True

    except AssertionError as ae:
        logging.error(f"[VALIDATION ERROR] Error de Validación de Calidad: {ae}")
        raise
    except Exception as e:
        logging.error(f"[VALIDATION ERROR] Error inesperado en Validación: {e}")
        raise
