"""Tests for the ML pipeline module."""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def sample_df():
    """Mini dataset for tests. Years span the temporal split boundary."""
    np.random.seed(42)
    n = 50
    return pd.DataFrame(
        {
            "borough": np.random.choice(["Camden", "Westminster", "Brent"], n),
            "major_category": np.random.choice(
                ["Violence Against the Person", "Theft and Handling", "Burglary"], n
            ),
            "minor_category": np.random.choice(
                ["Assault with injury", "Shoplifting", "Burglary in a dwelling"], n
            ),
            "year": np.random.choice([2008, 2010, 2012, 2014, 2015, 2016], n),
            "month": np.random.randint(1, 13, n),
            "total_crimes": np.random.poisson(15, n).astype(float),
        }
    )


class TestPreprocessing:
    def test_load_clean_data_csv(self, tmp_path, sample_df):
        from apps.backend.ml.preprocessing import load_clean_data

        path = tmp_path / "test.csv"
        sample_df.to_csv(path, index=False)
        df = load_clean_data(str(path))
        assert len(df) == 50
        assert "total_crimes" in df.columns

    def test_create_classification_target(self, sample_df):
        from apps.backend.ml.preprocessing import create_classification_target

        y = create_classification_target(sample_df, method="median")
        assert y.dtype == np.int64 or y.dtype == int
        assert set(np.unique(y)).issubset({0, 1})
        ratio = y.mean()
        assert 0.3 <= ratio <= 0.7

    def test_cyclical_encode_month(self, sample_df):
        from apps.backend.ml.preprocessing import cyclical_encode_month

        df = cyclical_encode_month(sample_df.copy())
        assert "month_sin" in df.columns
        assert "month_cos" in df.columns
        sums = (df["month_sin"] ** 2 + df["month_cos"] ** 2).values
        assert np.allclose(sums, 1.0, atol=1e-10)

    def test_prepare_features_has_six_inference_cols(self, sample_df):
        """prepare_features must return exactly the 6 cols the predict API sends."""
        from apps.backend.ml.preprocessing import prepare_features

        X = prepare_features(sample_df)
        assert list(X.columns) == [
            "borough",
            "major_category",
            "minor_category",
            "year",
            "month_sin",
            "month_cos",
        ]

    def test_build_preprocessor(self, sample_df):
        from apps.backend.ml.preprocessing import build_preprocessor

        preprocessor = build_preprocessor(["borough", "major_category"], ["year"])
        X = sample_df[["borough", "major_category", "year"]]
        X_t = preprocessor.fit_transform(X)
        assert X_t.shape[0] == 50
        assert X_t.shape[1] > 3

    def test_temporal_preprocess_and_split(self, sample_df):
        from apps.backend.ml.preprocessing import temporal_preprocess_and_split

        X_train, X_test, y_train, y_test, pre, df = temporal_preprocess_and_split(
            sample_df, train_until_year=2014
        )
        assert set(np.unique(y_train)).issubset({0, 1})
        assert set(np.unique(y_test)).issubset({0, 1})
        # train should contain years <= 2014
        assert (X_train["year"] <= 2014).all()
        assert (X_test["year"] > 2014).all()


class TestClassification:
    def test_train_logistic_regression(self, sample_df):
        from apps.backend.ml.preprocessing import (
            build_preprocessor,
            create_classification_target,
            prepare_features,
        )
        from apps.backend.ml.classification import train_logistic_regression

        X = prepare_features(sample_df)
        y = create_classification_target(sample_df)
        preprocessor = build_preprocessor(
            ["borough", "major_category", "minor_category"],
            ["year", "month_sin", "month_cos"],
        )
        X_t = preprocessor.fit_transform(X)
        model = train_logistic_regression(X_t[:40], y[:40])
        assert hasattr(model, "coef_")
        assert hasattr(model, "predict_proba")

    def test_evaluate_classification_returns_all_metrics(self, sample_df):
        from apps.backend.ml.preprocessing import (
            build_preprocessor,
            create_classification_target,
            prepare_features,
        )
        from apps.backend.ml.classification import (
            evaluate_classification,
            train_logistic_regression,
        )

        X = prepare_features(sample_df)
        y = create_classification_target(sample_df)
        preprocessor = build_preprocessor(
            ["borough", "major_category", "minor_category"],
            ["year", "month_sin", "month_cos"],
        )
        X_t = preprocessor.fit_transform(X)
        model = train_logistic_regression(X_t[:40], y[:40])
        metrics = evaluate_classification(model, X_t[40:], y[40:], "LogReg")
        for key in ["accuracy", "precision", "recall", "f1_score", "confusion_matrix"]:
            assert key in metrics, f"Missing metric: {key}"
        assert len(metrics["confusion_matrix"]) == 2
        assert len(metrics["confusion_matrix"][0]) == 2

    def test_train_crime_regressor(self, sample_df):
        from apps.backend.ml.preprocessing import (
            build_preprocessor,
            prepare_features,
        )
        from apps.backend.ml.classification import evaluate_regression, train_crime_regressor

        X = prepare_features(sample_df)
        y = sample_df["total_crimes"].values
        preprocessor = build_preprocessor(
            ["borough", "major_category", "minor_category"],
            ["year", "month_sin", "month_cos"],
        )
        X_t = preprocessor.fit_transform(X)
        model = train_crime_regressor(X_t[:40], y[:40])
        pred = model.predict(X_t[40:])
        metrics = evaluate_regression(model, X_t[40:], y[40:])

        assert len(pred) == 10
        assert "mae" in metrics
        assert "r2" in metrics


class TestInferenceConsistency:
    """The predict API must be able to transform a single row through the trained preprocessor."""

    def test_preprocessor_transform_single_inference_row(self, sample_df):
        from apps.backend.ml.preprocessing import (
            build_preprocessor,
            prepare_features,
        )

        # Fit preprocessor on training data
        X = prepare_features(sample_df)
        preprocessor = build_preprocessor(
            ["borough", "major_category", "minor_category"],
            ["year", "month_sin", "month_cos"],
        )
        preprocessor.fit_transform(X)

        # Simulate the exact row predict.py builds (6 cols, no lag)
        import numpy as np

        row = pd.DataFrame(
            [
                {
                    "borough": "Westminster",
                    "major_category": "Theft and Handling",
                    "minor_category": "Shoplifting",
                    "year": 2016,
                    "month_sin": np.sin(2 * np.pi * 6 / 12),
                    "month_cos": np.cos(2 * np.pi * 6 / 12),
                }
            ]
        )
        X_t = preprocessor.transform(row)  # must NOT raise
        assert X_t.shape[0] == 1
        assert X_t.shape[1] == X.shape[1] or X_t.shape == (1, preprocessor.transform(X).shape[1])
