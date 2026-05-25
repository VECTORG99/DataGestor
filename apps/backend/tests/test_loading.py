import pandas as pd
from pathlib import Path
from pandas import Timestamp

from apps.backend.pipeline.loading import save_clean_data


class TestSaveCleanData:
    def test_saves_csv_and_parquet(self, tmp_path):
        df = pd.DataFrame(
            {
                "borough": ["London"],
                "major_category": ["Theft"],
                "minor_category": ["Pickpocketing"],
                "year": [2020],
                "month": [1],
                "total_crimes": [100],
                "date": [Timestamp("2020-01-01")],
            }
        )
        result = save_clean_data(df, tmp_path)

        csv_path = Path(result["csv"])
        parquet_path = Path(result["parquet"])

        assert csv_path.exists()
        assert csv_path.suffix == ".csv"
        assert parquet_path.exists()
        assert parquet_path.suffix == ".parquet"

        # Verify content
        df_csv = pd.read_csv(csv_path)
        assert list(df_csv["borough"]) == ["London"]

    def test_creates_output_directory(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        df = pd.DataFrame(
            {
                "borough": ["London"],
                "major_category": ["Theft"],
                "minor_category": ["Pickpocketing"],
                "year": [2020],
                "month": [1],
                "total_crimes": [100],
                "date": [Timestamp("2020-01-01")],
            }
        )
        result = save_clean_data(df, nested)
        assert Path(result["csv"]).exists()
