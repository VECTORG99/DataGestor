"""
Módulo de Gestión de Etapas del Pipeline
Responsable de guardar copias de datos en diferentes etapas:
- RAW: datos originales sin modificaciones
- VALIDATED: datos que pasaron validaciones básicas
- PROCESSED: datos limpios y procesados

Este módulo NO modifica el flujo del pipeline, solo guarda copias de referencia.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Union, Dict, Optional, List
from datetime import datetime

from config import settings


class DataStageManager:
    """
    Gestiona el guardado de datos en diferentes etapas del pipeline.
    Crea automáticamente la estructura de carpetas necesaria.
    """

    def __init__(self, data_root: Union[str, Path] = None):
        if data_root is None:
            data_root = settings.DATA_DIR
        self.data_root = Path(data_root)
        self.raw_dir = settings.RAW_DIR
        self.validated_dir = settings.VALIDATED_DIR
        self.processed_dir = settings.PROCESSED_DIR

        self._create_directory_structure()

    def _create_directory_structure(self) -> None:
        """
        Crea automáticamente la estructura de carpetas si no existen.
        """
        for directory in [self.raw_dir, self.validated_dir, self.processed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logging.info(f"Directorio asegurado: {directory}")

    def save_raw_data(self, df: pd.DataFrame, filename: str = "london_crime_raw") -> Dict[str, str]:
        """
        Guarda los datos originales (RAW) sin modificaciones en Parquet.

        Características:
        - Formato: Parquet (compresión y eficiencia de almacenamiento)
        - Preserva exactamente los datos del origen
        - Previene sobrescrituras accidentales mediante versionado

        Args:
            df (pd.DataFrame): DataFrame con datos originales
            filename (str): Nombre base del archivo (sin extensión)

        Returns:
            dict[str, str]: Ruta del archivo guardado {'parquet': ...}
        """
        logging.info("=" * 70)
        logging.info("ETAPA RAW: Guardando datos originales")
        logging.info("=" * 70)

        try:
            parquet_path = self.raw_dir / f"{filename}.parquet"

            # Registrar información del dataset
            logging.info(f"Filas: {len(df)}")
            logging.info(f"Columnas: {list(df.columns)}")
            logging.info(
                f"Tamaño aproximado: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
            )

            df.to_parquet(parquet_path, index=False, compression=settings.EXPORT_COMPRESSION)
            logging.info(f"[OK] Datos RAW guardados: {parquet_path}")

            return {"parquet": str(parquet_path)}

        except Exception as e:
            logging.error(f"[ERROR] Error al guardar datos RAW: {e}")
            raise

    def validate_and_save_validated(
        self,
        df: pd.DataFrame,
        filename: str = "london_crime_validated",
        validation_report_filename: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Valida datos básicos y guarda los datos validados en Parquet.

        Validaciones aplicadas:
        - Columnas obligatorias existentes
        - Tipos de datos válidos
        - Ausencia de valores nulos críticos
        - Duplicados detectados pero NO eliminados
        - Rangos válidos para campos numéricos

        Args:
            df (pd.DataFrame): DataFrame a validar
            filename (str): Nombre base del archivo validado
            validation_report_filename (str): Nombre del reporte (None = sin reporte)

        Returns:
            dict[str, str]: Rutas de archivos guardados
        """
        logging.info("=" * 70)
        logging.info("ETAPA VALIDATED: Validando datos y guardando")
        logging.info("=" * 70)

        validation_results = {
            "total_rows": len(df),
            "validations": {},
            "invalid_records": [],
            "issues": [],
        }

        try:
            expected_columns = settings.EXPECTED_COLUMNS_RAW

            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                msg = f"Columnas faltantes: {missing_columns}"
                logging.warning(f"[WARN] {msg}")
                validation_results["issues"].append(msg)
            else:
                logging.info("[OK] Todas las columnas obligatorias presentes")
                validation_results["validations"]["required_columns"] = True

            # 2. Validar tipos de datos
            type_validation = self._validate_data_types(df)
            validation_results["validations"].update(type_validation)

            # 3. Validar valores nulos
            null_validation = self._validate_null_values(df)
            validation_results["validations"].update(null_validation)

            # 4. Detectar duplicados (sin eliminar)
            duplicates_info = self._check_duplicates(df)
            validation_results["validations"].update(duplicates_info)

            # 5. Validar rangos
            range_validation = self._validate_value_ranges(df)
            validation_results["validations"].update(range_validation)

            parquet_path = self.validated_dir / f"{filename}.parquet"
            df.to_parquet(parquet_path, index=False, compression=settings.EXPORT_COMPRESSION)
            logging.info(f"[OK] Datos VALIDATED guardados: {parquet_path}")

            result_paths = {"parquet": str(parquet_path)}

            # Guardar reporte de validación si se solicita
            if validation_report_filename:
                report_path = self.validated_dir / f"{validation_report_filename}.txt"
                self._save_validation_report(validation_results, report_path)
                result_paths["validation_report"] = str(report_path)

            return result_paths

        except Exception as e:
            logging.error(f"[ERROR] Error al validar/guardar datos VALIDATED: {e}")
            raise

    def save_processed_data(
        self,
        df: pd.DataFrame,
        filename: str = "london_crime_aggregated",
        formats: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        if formats is None:
            formats = settings.EXPORT_FORMATS

        logging.info("=" * 70)
        logging.info("ETAPA PROCESSED: Guardando datos limpios")
        logging.info("=" * 70)

        result_paths = {}

        try:
            expected_columns = settings.EXPECTED_COLUMNS_PROCESSED
            missing = [col for col in expected_columns if col not in df.columns]
            if missing:
                logging.warning(f"[WARN] Columnas faltantes: {missing}")
            else:
                logging.info("[OK] Estructura de datos validada")

            logging.info(f"Filas procesadas: {len(df)}")
            logging.info(f"Columnas: {list(df.columns)}")
            logging.info(
                f"Tamaño aproximado: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
            )

            # Guardar en Parquet si se solicita
            if "parquet" in formats:
                parquet_path = self.processed_dir / f"{filename}.parquet"
                df.to_parquet(parquet_path, index=False, compression=settings.EXPORT_COMPRESSION)
                logging.info(f"[OK] Datos PROCESSED guardados (Parquet): {parquet_path}")
                result_paths["parquet"] = str(parquet_path)

            # Guardar en CSV si se solicita
            if "csv" in formats:
                csv_path = self.processed_dir / f"{filename}.csv"
                df.to_csv(csv_path, index=False)
                logging.info(f"[OK] Datos PROCESSED guardados (CSV): {csv_path}")
                result_paths["csv"] = str(csv_path)

            return result_paths

        except Exception as e:
            logging.error(f"[ERROR] Error al guardar datos PROCESSED: {e}")
            raise

    def _validate_data_types(self, df: pd.DataFrame) -> Dict[str, bool]:
        logging.info("Validando tipos de datos...")
        results = {"data_types_valid": True}

        TYPE_CHECKS = {
            "year": ["int", "Int64"],
            "month": ["int", "Int64"],
            "value": ["float", "float64"],
            "borough": ["string", "object"],
            "major_category": ["string", "object"],
            "minor_category": ["string", "object"],
        }

        for col, expected_types in TYPE_CHECKS.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                is_valid = any(exp_type in actual_type for exp_type in expected_types)
                if is_valid:
                    logging.info(f"  [OK] {col}: {actual_type}")
                else:
                    logging.warning(
                        f"  [WARN] {col}: tipo {actual_type}, esperado {expected_types}"
                    )
                    results["data_types_valid"] = False

        return results

    def _validate_null_values(self, df: pd.DataFrame) -> Dict[str, int]:
        logging.info("Validando valores nulos...")
        results = {}

        for col in settings.CRITICAL_COLUMNS:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                results[f"nulls_{col}"] = null_count
                if null_count > 0:
                    logging.warning(f"  [WARN] {col}: {null_count} valores nulos")
                else:
                    logging.info(f"  [OK] {col}: sin valores nulos")

        return results

    def _check_duplicates(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Detecta registros duplicados.

        Returns:
            dict: Información sobre duplicados
        """
        logging.info("Detectando duplicados...")

        all_duplicates = df.duplicated().sum()
        results = {"total_duplicates": all_duplicates}

        if all_duplicates > 0:
            logging.warning(f"  [WARN] {all_duplicates} registros duplicados detectados")
        else:
            logging.info("  [OK] No hay registros duplicados")

        return results

    def _validate_value_ranges(self, df: pd.DataFrame) -> Dict[str, bool]:
        logging.info("Validando rangos de valores...")
        results = {"ranges_valid": True}

        if "month" in df.columns:
            invalid_months = df["month"].notna() & ~df["month"].between(
                settings.VALIDATION_MONTH_MIN, settings.VALIDATION_MONTH_MAX
            )
            if invalid_months.sum() > 0:
                logging.warning(
                    f"  [WARN] {invalid_months.sum()} meses fuera de rango "
                    f"({settings.VALIDATION_MONTH_MIN}-{settings.VALIDATION_MONTH_MAX})"
                )
                results["ranges_valid"] = False
            else:
                logging.info(
                    f"  [OK] Meses en rango válido "
                    f"({settings.VALIDATION_MONTH_MIN}-{settings.VALIDATION_MONTH_MAX})"
                )

        if "year" in df.columns:
            year_min = df["year"].min()
            year_max = df["year"].max()
            logging.info(f"  [OK] Años: {year_min} - {year_max}")

        if "value" in df.columns:
            negative_values = (df["value"] < 0).sum()
            if negative_values > 0:
                logging.warning(f"  [WARN] {negative_values} valores negativos en 'value'")
                results["ranges_valid"] = False
            else:
                logging.info("  [OK] Sin valores negativos")

        return results

    def _save_validation_report(
        self, validation_results: Dict, report_path: Union[str, Path]
    ) -> None:
        """
        Guarda un reporte de validación en formato texto.

        Args:
            validation_results (dict): Resultados de validación
            report_path (str | Path): Ruta del archivo de reporte
        """
        report_path = Path(report_path)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("REPORTE DE VALIDACION DE DATOS\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Total de filas: {validation_results['total_rows']}\n\n")

            f.write("VALIDACIONES REALIZADAS:\n")
            f.write("-" * 70 + "\n")
            for key, value in validation_results["validations"].items():
                status = "[OK] PASO" if value is True else f"[WARN] {value}"
                f.write(f"  {key}: {status}\n")

            if validation_results["issues"]:
                f.write("\nPROBLEMAS DETECTADOS:\n")
                f.write("-" * 70 + "\n")
                for issue in validation_results["issues"]:
                    f.write(f"  - {issue}\n")

        logging.info(f"Reporte de validación guardado: {report_path}")
