"""add need auth

Revision ID: e91887eae42f
Revises: 370ed17ef4f5
Create Date: 2024-01-31 22:20:27.309999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e91887eae42f'
down_revision: Union[str, None] = '370ed17ef4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('message_condition', sa.Column('need_auth', sa.Boolean(), nullable=True))
    op.add_column('tg_users', sa.Column('last_state', sa.Integer(), nullable=True))
    op.add_column('tg_users', sa.Column('lists', sa.ARRAY(sa.Integer()), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tg_users', 'lists')
    op.drop_column('tg_users', 'last_state')
    op.drop_column('message_condition', 'need_auth')
    # ### end Alembic commands ###