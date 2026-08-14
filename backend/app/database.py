import sqlite3
from pathlib import Path

DATABASE_PATH = Path("app/ad_insight.db")

def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def initialize_database() -> None:
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS import_jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        status TEXT NOT NULL,
        imported_rows INTEGER NOT NULL DEFAULT 0,
        error_count INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS ad_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        import_job_id INTEGER NOT NULL,
        result_date TEXT NOT NULL,
        campaign TEXT NOT NULL,
        impressions INTEGER NOT NULL,
        clicks INTEGER NOT NULL,
        cost INTEGER NOT NULL,
        conversions INTEGER NOT NULL,
        revenue INTEGER NOT NULL,
        FOREIGN KEY (import_job_id)
            REFERENCES import_jobs(id),
        UNIQUE(
        import_job_id,
        result_date,
        campaign
        )
    )
    """
    )

    connection.commit()
    connection.close()
