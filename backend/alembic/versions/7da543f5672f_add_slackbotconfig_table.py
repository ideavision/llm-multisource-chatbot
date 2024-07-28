"""Add SlackBotConfig table

Revision ID: 7da543f5672f
Revises: febe9eaa0644
Create Date: 2023-12-24 16:34:17.526128

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7da543f5672f"
down_revision = "febe9eaa0644"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "slack_bot_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("passist_id", sa.Integer(), nullable=True),
        sa.Column(
            "channel_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["passist_id"],
            ["passist.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("slack_bot_config")
