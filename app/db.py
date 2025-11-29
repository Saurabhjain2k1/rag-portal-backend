# app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.engine.url import make_url

from .config import settings

class Base(DeclarativeBase):
    pass


url = make_url(settings.database_url)

engine = create_engine(
    url,
    echo=False,
    connect_args={"sslmode": "require"},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
