"""forcibly remove more enum types from postgres

Revision ID: 77d07dffae64
Revises: d61e513bef0a
Create Date: 2023-12-01 12:33:01.999617

"""
from alembic import op
from sqlalchemy import String


# revision identifiers, used by Alembic.
revision = "77d07dffae64"
down_revision = "d61e513bef0a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # we directly changed some previous migrations. This caused some users to have native enums
    # while others wouldn't. This has caused some issues when adding new fields to these enums.
    # This migration manually changes the enum types to ensure that nobody uses native enums.
    op.alter_column("query_event", "selected_search_flow", type_=String)
    op.alter_column("query_event", "feedback", type_=String)
    op.alter_column("document_retrieval_feedback", "feedback", type_=String)
    op.execute("DROP TYPE IF EXISTS searchtype")
    op.execute("DROP TYPE IF EXISTS qafeedbacktype")
    op.execute("DROP TYPE IF EXISTS searchfeedbacktype")


def downgrade() -> None:
    # We don't want Native Enums, do nothing
    pass
