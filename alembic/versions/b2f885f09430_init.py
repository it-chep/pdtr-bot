"""init

Revision ID: 64b96a3bd450
Revises:
Create Date: 2023-10-17 23:15:20.562886

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64b96a3bd450'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("right_answer", sa.Integer, nullable=False),
        sa.Column("answers", sa.ARRAY(sa.Integer), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("questions")
