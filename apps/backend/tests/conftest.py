import pandas as pd
import pytest


@pytest.fixture
def sample_raw_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "borough": [
                "City of London",
                "Westminster",
                None,
                "Kensington And Chelsea",
                "Camden",
                "Westminster",
            ],
            "major_category": [
                "Theft and Handling",
                "Violence Against the Person",
                "Burglary",
                None,
                "Theft and Handling",
                "Theft and Handling",
            ],
            "minor_category": [
                "Pickpocketing",
                "Assault",
                None,
                "Burglary",
                "Shoplifting",
                "Pickpocketing",
            ],
            "value": [10, 5, -3, 15, 0, 10],
            "year": [2016, 2015, 2020, 2017, 2016, 2016],
            "month": [1, 13, 6, 8, 1, 1],
            "lsoa_code": [
                "E01000001",
                "E01000002",
                "E01000003",
                "E01000004",
                "E01000001",
                "E01000001",
            ],
        }
    )


@pytest.fixture
def sample_clean_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "borough": pd.array(["City of London", "Westminster", "Camden"], dtype="string"),
            "major_category": pd.array(
                [
                    "Theft and Handling",
                    "Violence Against the Person",
                    "Theft and Handling",
                ],
                dtype="string",
            ),
            "minor_category": pd.array(["Pickpocketing", "Assault", "Shoplifting"], dtype="string"),
            "total_crimes": pd.array([10.0, 5.0, 0.0], dtype="float64"),
            "year": pd.array([2016, 2015, 2016], dtype="Int64"),
            "month": pd.array([1, 12, 1], dtype="Int64"),
            "date": pd.to_datetime(["2016-01-01", "2015-12-01", "2016-01-01"]),
        }
    )


@pytest.fixture
def sample_clean_df_with_duplicates() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "borough": ["City of London", "City of London", "Westminster"],
            "major_category": [
                "Theft and Handling",
                "Theft and Handling",
                "Violence Against the Person",
            ],
            "minor_category": ["Pickpocketing", "Pickpocketing", "Assault"],
            "total_crimes": [10, 10, 5],
            "year": [2016, 2016, 2015],
            "month": [1, 1, 12],
            "date": pd.to_datetime(["2016-01-01", "2016-01-01", "2015-12-01"]),
        }
    )
