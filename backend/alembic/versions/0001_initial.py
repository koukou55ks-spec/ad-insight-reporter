"""create initial ad insight tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-21
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("imported_rows", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_table(
        "ad_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("import_job_id", sa.Integer(), nullable=False),
        sa.Column("result_date", sa.String(length=10), nullable=False),
        sa.Column("campaign", sa.String(length=255), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("cost", sa.Integer(), nullable=False),
        sa.Column("conversions", sa.Integer(), nullable=False),
        sa.Column("revenue", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["import_job_id"], ["import_jobs.id"]),
        sa.UniqueConstraint(
            "import_job_id",
            "result_date",
            "campaign",
            name="uq_ad_results_import_date_campaign",
        ),
    )


def downgrade() -> None:
    op.drop_table("ad_results")
    op.drop_table("import_jobs")
