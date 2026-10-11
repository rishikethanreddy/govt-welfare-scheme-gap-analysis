import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# We can fallback to SQLite if DATABASE_URL is not provided or Postgres is unavailable during dev.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./welfare_awareness.db")
# Note: For SQLite, check_same_thread=False is needed if multiple threads access it. 
# It is ignored by Postgres.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
