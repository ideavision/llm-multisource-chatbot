"""Passist Datetime Aware

Revision ID: 30c1d5744104
Revises: 7f99be1cb9f5
Create Date: 2023-12-16 23:21:01.283424

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "30c1d5744104"
down_revision = "7f99be1cb9f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("passist", sa.Column("datetime_aware", sa.Boolean(), nullable=True))
    op.execute("UPDATE passist SET datetime_aware = TRUE")
    op.alter_column("passist", "datetime_aware", nullable=False)
    op.create_index(
        "_default_passist_name_idx",
        "passist",
        ["name"],
        unique=True,
        postgresql_where=sa.text("default_passist = true"),
    )


def downgrade() -> None:
    op.drop_index(
        "_default_passist_name_idx",
        table_name="passist",
        postgresql_where=sa.text("default_passist = true"),
    )
    op.drop_column("passist", "datetime_aware")
