import pandas as pd

NUMERIC_COLUMNS = [
    "impressions",
    "clicks",
    "cost",
    "conversions",
    "revenue",
]


def validate_dataframe(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    # 日付の検証
    invalid_dates = pd.to_datetime(
        df["date"],
        errors="coerce",
    ).isna()

    for index in df.index[invalid_dates]:
        errors.append(f"{index + 2}行目: dateが正しい日付ではありません")

    # 数値の検証
    for column in NUMERIC_COLUMNS:
        converted = pd.to_numeric(df[column], errors="coerce")

        invalid_numbers = converted.isna()

        for index in df.index[invalid_numbers]:
            errors.append(f"{index + 2}行目:{column}が数値ではありません")

        negative_numbers = converted < 0

        for index in df.index[negative_numbers]:
            errors.append(f"{index + 2}行目:{column}は0以上にしてください")

    # クリック数が表示回数を超えていないか
    impressions = pd.to_numeric(
        df["impressions"],
        errors="coerce",
    )
    clicks = pd.to_numeric(
        df["clicks"],
        errors="coerce",
    )

    invalid_clicks = clicks > impressions

    for index in df.index[invalid_clicks]:
        errors.append(f"{index + 2}行目: clicksがimpressionsを超えています")

    # 成果数がクリックを超えていないか
    conversions = pd.to_numeric(
        df["conversions"],
        errors="coerce",
    )

    invalid_conversions = conversions > clicks

    for index in df.index[invalid_conversions]:
        errors.append(f"{index + 2}行目: conversionsがcllicksを超えています")

    return errors


def summarize_data(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()

    data["date"] = pd.to_datetime(data["date"])

    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column])

    summary = data.groupby("campaign", as_index=False).agg(
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        cost=("cost", "sum"),
        conversions=("conversions", "sum"),
        revenue=("revenue", "sum"),
    )

    summary["ctr"] = summary["clicks"].div(summary["impressions"]).mul(100)

    summary["cpa"] = summary["cost"].div(summary["conversions"])

    summary["roas"] = summary["revenue"].div(summary["cost"]).mul(100)

    summary = summary.replace(
        [float("inf"), -float("inf")],
        None,
    )

    return summary.round(2)


def detect_anomalies(df: pd.DataFrame) -> list[dict[str, str]]:
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])

    latest_date = data["date"].max()
    current_start = latest_date - pd.Timedelta(days=6)
    previous_end = current_start - pd.Timedelta(days=1)
    previous_start = previous_end - pd.Timedelta(days=6)

    current_data = data[(data["date"] >= current_start) & (data["date"] <= latest_date)]

    previous_data = data[(data["date"] >= previous_start) & (data["date"] <= previous_end)]

    if current_data.empty or previous_data.empty:
        return []

    current_summary = summarize_data(current_data)
    previous_summary = summarize_data(previous_data)

    current_summary = current_summary[["campaign", "cost", "conversions", "cpa", "roas"]].rename(
        columns={
            "cost": "current_cost",
            "conversions": "current_conversions",
            "cpa": "current_cpa",
            "roas": "current_roas",
        }
    )

    previous_summary = previous_summary[["campaign", "cost", "conversions", "cpa", "roas"]].rename(
        columns={
            "cost": "previous_cost",
            "conversions": "previous_conversions",
            "cpa": "previous_cpa",
            "roas": "previous_roas",
        }
    )

    comparison = current_summary.merge(
        previous_summary,
        on="campaign",
        how="inner",
    )

    alerts: list[dict[str, str]] = []

    for row in comparison.to_dict(orient="records"):
        campaign = row["campaign"]

        # 1. CPAが30%以上悪化
        previous_cpa = row["previous_cpa"]
        current_cpa = row["current_cpa"]

        if not pd.isna(previous_cpa) and not pd.isna(current_cpa) and previous_cpa > 0:
            cpa_change = (current_cpa - previous_cpa) / previous_cpa * 100

            if cpa_change >= 30:
                alerts.append(
                    {
                        "campaign": campaign,
                        "type": "CPA",
                        "message": (f"CPAが前週比{cpa_change:.1f}%悪化"),
                        "previous_value": f"{previous_cpa:.2f}",
                        "current_value": f"{current_cpa:.2f}",
                        "unit": "円",
                    }
                )

        # 2. ROASが20%以上低下
        previous_roas = row["previous_roas"]
        current_roas = row["current_roas"]

        if not pd.isna(previous_roas) and not pd.isna(current_roas) and previous_roas > 0:
            roas_change = (current_roas - previous_roas) / previous_roas * 100

            if roas_change <= -20:
                alerts.append(
                    {
                        "campaign": campaign,
                        "type": "ROAS",
                        "message": (f"ROASが前週比{abs(roas_change):.1f}%低下"),
                        "previous_value": f"{previous_roas:.2f}",
                        "current_value": f"{current_roas:.2f}",
                        "unit": "%",
                    }
                )

        # 3. 広告費が増加し、CVが減少
        previous_cost = row["previous_cost"]
        current_cost = row["current_cost"]
        previous_conversions = row["previous_conversions"]
        current_conversions = row["current_conversions"]

        if current_cost > previous_cost and current_conversions < previous_conversions:
            alerts.append(
                {
                    "campaign": campaign,
                    "type": "費用・CV",
                    "message": ("広告費が増加した一方でCV数が減少"),
                    "previous_value": (
                        f"費用{previous_cost:.0f}円・CV{previous_conversions:.0f}件"
                    ),
                    "current_value": (f"費用{current_cost:.0f}円・CV{current_conversions:.0f}件"),
                    "unit": "",
                }
            )

    return alerts
