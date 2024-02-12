"""create lessons and perrmission on user

Revision ID: 59f64af975da
Revises: faae710a48a8
Create Date: 2023-11-12 16:11:42.884297

"""
from typing import Sequence, Union
from models import UserPermissions
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils

# revision identifiers, used by Alembic.
revision: str = '59f64af975da'
down_revision: Union[str, None] = 'faae710a48a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lessons',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('lesson_number', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.String(length=255), nullable=True),
    sa.Column('tg_file_id', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('tg_users', sa.Column('permissions', sqlalchemy_utils.types.choice.ChoiceType(
        UserPermissions, impl=sa.Integer()
    ), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tg_users', 'permissions')
    op.drop_table('lessons')
    # ### end Alembic commands ###