import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    text,
    UniqueConstraint,
    create_engine,
)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///app/ad_insight.db",
)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

metadata = MetaData()

import_jobs = Table(
    "import_jobs",
    metadata,
    # SQLAlchemy maps this to an auto-incrementing identity column on PostgreSQL.
    Column("id", Integer, primary_key=True),
    Column("file_name", String(255), nullable=False),
    Column("status", String(32), nullable=False),
    Column("imported_rows", Integer, nullable=False, default=0),
    Column("error_count", Integer, nullable=False, default=0),
    Column(
        "created_at",
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
)

ad_results = Table(
    "ad_results",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "import_job_id",
        Integer,
        ForeignKey("import_jobs.id"),
        nullable=False,
    ),
    Column("result_date", String(10), nullable=False),
    Column("campaign", String(255), nullable=False),
    Column("impressions", Integer, nullable=False),
    Column("clicks", Integer, nullable=False),
    Column("cost", Integer, nullable=False),
    Column("conversions", Integer, nullable=False),
    Column("revenue", Integer, nullable=False),
    UniqueConstraint(
        "import_job_id",
        "result_date",
        "campaign",
        name="uq_ad_results_import_date_campaign",
    ),
)


def get_connection():
    """Return a SQLAlchemy connection for SQLite or PostgreSQL."""
    return engine.connect()


def initialize_database() -> None:
    """Create the schema if it does not exist yet."""
    metadata.create_all(engine)
