from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings


# TODO 1: создать engine
engine = create_engine(
    settings.database_url,
    echo=settings.sql_echo
)
# TODO 2: создать SessionLocal
SessionLocal = sessionmaker(engine)