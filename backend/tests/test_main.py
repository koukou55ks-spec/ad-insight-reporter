import json
from datetime import date
from decimal import Decimal

import pandas as pd

from app import main


class RecordingConnection:
    def __init__(self, *, execute_error: Exception | None = None) -> None:
        self.execute_error = execute_error
        self.closed = False
        self.calls: list[tuple[object, object | None]] = []

    def execute(self, statement, parameters=None):
        if self.execute_error is not None:
            raise self.execute_error
        self.calls.append((statement, parameters))

    def close(self) -> None:
        self.closed = True


def test_health_check_returns_503_and_closes_connection(monkeypatch):
    connection = RecordingConnection(execute_error=RuntimeError("db unavailable"))
    monkeypatch.setattr(main, "get_connection", lambda: connection)

    response = main.health_check()

    assert response.status_code == 503
    assert json.loads(response.body) == {
        "status": "error",
        "database": "unavailable",
    }
    assert connection.closed is True


def test_health_check_returns_200_and_closes_connection(monkeypatch):
    connection = RecordingConnection()
    monkeypatch.setattr(main, "get_connection", lambda: connection)

    response = main.health_check()

    assert response.status_code == 200
    assert json.loads(response.body) == {"status": "ok", "database": "ok"}
    assert connection.closed is True


def test_health_check_handles_connection_failure(monkeypatch):
    def fail_to_connect():
        raise RuntimeError("cannot connect")

    monkeypatch.setattr(main, "get_connection", fail_to_connect)

    response = main.health_check()

    assert response.status_code == 503


def test_save_ad_results_uses_native_date_and_decimal_values():
    connection = RecordingConnection()
    dataframe = pd.DataFrame(
        [
            {
                "date": "2026-08-21",
                "campaign": "商品A",
                "impressions": 1000,
                "clicks": 25,
                "cost": "1234.56",
                "conversions": 3,
                "revenue": "7890.12",
            }
        ]
    )

    main.save_ad_results(connection, dataframe, import_job_id=42)

    records = connection.calls[0][1]
    assert records[0]["result_date"] == date(2026, 8, 21)
    assert records[0]["cost"] == Decimal("1234.56")
    assert records[0]["revenue"] == Decimal("7890.12")
