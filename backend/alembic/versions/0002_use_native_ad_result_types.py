"""use native date and decimal types for ad results

Revision ID: 0002_native_types
Revises: 0001_initial
Create Date: 2026-08-21
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_native_types"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "ad_results",
        "result_date",
        existing_type=sa.String(length=10),
        type_=sa.Date(),
        existing_nullable=False,
        postgresql_using="result_date::date",
    )
    op.alter_column(
        "ad_results",
        "cost",
        existing_type=sa.Integer(),
        type_=sa.Numeric(precision=18, scale=2),
        existing_nullable=False,
        postgresql_using="cost::numeric(18, 2)",
    )
    op.alter_column(
        "ad_results",
        "revenue",
        existing_type=sa.Integer(),
        type_=sa.Numeric(precision=18, scale=2),
        existing_nullable=False,
        postgresql_using="revenue::numeric(18, 2)",
    )


def downgrade() -> None:
    op.alter_column(
        "ad_results",
        "revenue",
        existing_type=sa.Numeric(precision=18, scale=2),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="revenue::integer",
    )
    op.alter_column(
        "ad_results",
        "cost",
        existing_type=sa.Numeric(precision=18, scale=2),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="cost::integer",
    )
    op.alter_column(
        "ad_results",
        "result_date",
        existing_type=sa.Date(),
        type_=sa.String(length=10),
        existing_nullable=False,
        postgresql_using="result_date::text",
    )
