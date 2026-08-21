from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    text,
)

from app.settings import settings

engine = create_engine(
    settings.database_url,
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
    Column("result_date", Date, nullable=False),
    Column("campaign", String(255), nullable=False),
    Column("impressions", Integer, nullable=False),
    Column("clicks", Integer, nullable=False),
    Column("cost", Numeric(18, 2), nullable=False),
    Column("conversions", Integer, nullable=False),
    Column("revenue", Numeric(18, 2), nullable=False),
    UniqueConstraint(
        "import_job_id",
        "result_date",
        "campaign",
        name="uq_ad_results_import_date_campaign",
    ),
)


def get_connection():
    """Return a SQLAlchemy connection to PostgreSQL."""
    return engine.connect()
