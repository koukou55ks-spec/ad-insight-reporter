import pandas as pd

from app.analysis import validate_dataframe


def make_valid_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2026-08-01",
                "campaign": "商品A",
                "impressions": 10000,
                "clicks": 300,
                "cost": 50000,
                "conversions": 20,
                "revenue": 120000,
            },
            {
                "date": "2026-08-01",
                "campaign": "商品B",
                "impressions": 8000,
                "clicks": 180,
                "cost": 40000,
                "conversions": 8,
                "revenue": 50000,
            },
        ]
    )


def test_validate_dataframe_accepts_validate_data():
    df = make_valid_dataframe()

    errors = validate_dataframe(df)

    assert errors == []
