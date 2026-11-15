from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# Base class for models
Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()