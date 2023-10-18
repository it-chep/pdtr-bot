from alembic import context
from sqlalchemy import create_engine, MetaData

from questions.models import Question

metadata = MetaData()

table = Question.__tablename__

target_metadata = metadata

config = context.config
db_url = config.get_main_option("sqlalchemy.url")

engine = create_engine(db_url)

with engine.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
