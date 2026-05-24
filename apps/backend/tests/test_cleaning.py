import pandas as pd
import numpy as np
from pandas import Timestamp

from apps.backend.pipeline.cleaning import (
    standardize_column_names,
    handle_null_values,
    validate_data_types,
    validate_value_ranges,
    normalize_text_fields,
    detect_and_remove_duplicates,
    create_date_column,
    detect_outliers,
    remove_unnecessary_columns,
    clean_and_transform_data,
    validate_data_quality,
)


# ---------------------------------------------------------------------------
# standardize_column_names
# ---------------------------------------------------------------------------

class TestStandardizeColumnNames:
    def test_converts_to_snake_case(self):
        df = pd.DataFrame({"Borough Name": [1], "Major-Category": [2]})
        result = standardize_column_names(df)
        assert list(result.columns) == ["borough_name", "major_category"]

    def test_lowercases(self):
        df = pd.DataFrame({"BOROUGH": [1]})
        result = standardize_column_names(df)
        assert "borough" in result.columns


# ---------------------------------------------------------------------------
# handle_null_values
# ---------------------------------------------------------------------------

class TestHandleNullValues:
    def test_removes_rows_with_null_in_critical_columns(self, sample_raw_df):
        result = handle_null_values(sample_raw_df)
        assert result["borough"].notna().all()
        assert result["major_category"].notna().all()
        assert result["value"].notna().all()

    def test_removes_null_string_values(self):
        df = pd.DataFrame({
            "borough": ["City of London", "NULL", "Unknown"],
            "major_category": ["Theft", "Burglary", "Violence"],
            "value": [1.0, 2.0, 3.0],
            "year": [2016, 2016, 2016],
            "month": [1, 2, 3],
        })
        result = handle_null_values(df)
        assert len(result) == 1
        assert result.iloc[0]["borough"] == "City of London"


# ---------------------------------------------------------------------------
# validate_data_types
# ---------------------------------------------------------------------------

class TestValidateDataTypes:
    def test_converts_year_to_int64(self, sample_raw_df):
        df = sample_raw_df.dropna(subset=["year", "month", "value"])
        result = validate_data_types(df)
        assert result["year"].dtype in ("Int64", "int64")
        assert result["month"].dtype in ("Int64", "int64")

    def test_converts_value_to_float64(self, sample_raw_df):
        df = sample_raw_df.dropna(subset=["year", "month", "value"])
        result = validate_data_types(df)
        assert result["value"].dtype == "float64"

    def test_converts_text_columns_to_string(self, sample_raw_df):
        df = sample_raw_df.dropna(subset=["borough", "major_category"])
        result = validate_data_types(df)
        assert result["borough"].dtype == "string"
        assert result["major_category"].dtype == "string"


# ---------------------------------------------------------------------------
# validate_value_ranges
# ---------------------------------------------------------------------------

class TestValidateValueRanges:
    def test_removes_invalid_months(self, sample_raw_df):
        df = sample_raw_df.dropna(subset=["year", "month", "value"])
        result = validate_value_ranges(df)
        assert (result["month"].between(1, 12)).all()

    def test_removes_negative_values(self):
        df = pd.DataFrame({
            "borough": ["X"], "major_category": ["Y"],
            "value": [-5], "year": [2016], "month": [1],
        })
        result = validate_value_ranges(df)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# normalize_text_fields
# ---------------------------------------------------------------------------

class TestNormalizeTextFields:
    def test_title_case_and_strip(self):
        df = pd.DataFrame({
            "borough": ["  city of london  "],
            "major_category": ["theft and handling"],
            "minor_category": ["pickpocketing"],
        })
        result = normalize_text_fields(df)
        # title case + borough correction: "City Of London" -> "City of London"
        assert result["borough"].iloc[0] == "City of London"

    def test_borough_corrections(self):
        df = pd.DataFrame({
            "borough": ["Kensington And Chelsea"],
            "major_category": ["Theft"],
            "minor_category": ["Pickpocketing"],
        })
        result = normalize_text_fields(df)
        assert result["borough"].iloc[0] == "Kensington and Chelsea"


# ---------------------------------------------------------------------------
# detect_and_remove_duplicates
# ---------------------------------------------------------------------------

class TestDetectAndRemoveDuplicates:
    def test_removes_exact_duplicates(self, sample_clean_df_with_duplicates):
        result = detect_and_remove_duplicates(sample_clean_df_with_duplicates)
        assert len(result) == 2  # City of London aparece solo una vez

    def test_removes_subset_duplicates(self):
        df = pd.DataFrame({
            "borough": ["A", "A", "B"],
            "major_category": ["X", "X", "Y"],
            "minor_category": ["foo", "bar", "baz"],
            "value": [1, 2, 3],
            "year": [2016, 2016, 2015],
            "month": [1, 1, 12],
        })
        result = detect_and_remove_duplicates(df)
        assert len(result) == 2  # A/X/2016/1 duplicado, conserva el primero


# ---------------------------------------------------------------------------
# create_date_column
# ---------------------------------------------------------------------------

class TestCreateDateColumn:
    def test_creates_date_from_year_month(self):
        df = pd.DataFrame({"year": [2016, 2015], "month": [1, 12]})
        result = create_date_column(df)
        assert "date" in result.columns
        assert result["date"].iloc[0] == Timestamp("2016-01-01")
        assert result["date"].iloc[1] == Timestamp("2015-12-01")


# ---------------------------------------------------------------------------
# detect_outliers
# ---------------------------------------------------------------------------

class TestDetectOutliers:
    def test_detects_outliers_with_iqr(self):
        df = pd.DataFrame({"value": [1, 2, 1, 2, 1, 2, 100]})
        info = detect_outliers(df, method="iqr")
        assert info["outliers_detected"] >= 1
        assert 100 in info["outlier_values"]

    def test_returns_empty_if_no_value_column(self):
        df = pd.DataFrame({"x": [1]})
        info = detect_outliers(df)
        assert info["outliers_detected"] == 0


# ---------------------------------------------------------------------------
# remove_unnecessary_columns
# ---------------------------------------------------------------------------

class TestRemoveUnnecessaryColumns:
    def test_keeps_only_expected_columns(self):
        df = pd.DataFrame({
            "borough": ["A"], "major_category": ["B"], "minor_category": ["C"],
            "year": [2016], "month": [1], "value": [10], "date": [Timestamp("2016-01-01")],
            "trash": ["x"], "lsoa_code": ["E01"],
        })
        result = remove_unnecessary_columns(df)
        assert "trash" not in result.columns
        assert "lsoa_code" not in result.columns
        assert set(result.columns) == {"borough", "major_category", "minor_category", "year", "month", "value", "date"}


# ---------------------------------------------------------------------------
# clean_and_transform_data  (integración)
# ---------------------------------------------------------------------------

class TestCleanAndTransformData:
    def test_full_pipeline_returns_clean_dataframe(self, sample_raw_df):
        result = clean_and_transform_data(sample_raw_df)
        assert not result.empty
        assert result.isnull().sum().sum() == 0
        for col in ["borough", "major_category", "minor_category", "year", "month", "value", "date"]:
            assert col in result.columns
        assert (result["month"].between(1, 12)).all()
        assert (result["value"] >= 0).all()

    def test_no_outliers_removed_by_default(self, sample_raw_df):
        result = clean_and_transform_data(sample_raw_df)
        assert "date" in result.columns


# ---------------------------------------------------------------------------
# validate_data_quality
# ---------------------------------------------------------------------------

class TestValidateDataQuality:
    def test_passes_for_clean_dataframe(self, sample_clean_df):
        assert validate_data_quality(sample_clean_df) is True

    def test_raises_for_missing_column(self, sample_clean_df):
        bad = sample_clean_df.drop(columns=["date"])
        import pytest as _pytest
        with _pytest.raises(AssertionError):
            validate_data_quality(bad)

    def test_raises_for_null_values(self, sample_clean_df):
        bad = sample_clean_df.copy()
        bad.loc[0, "borough"] = None
        import pytest as _pytest
        with _pytest.raises(AssertionError):
            validate_data_quality(bad)
