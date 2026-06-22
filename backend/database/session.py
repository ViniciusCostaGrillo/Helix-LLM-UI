import os
from sqlalchemy.orm import declarative_base
from backend.database.sharding import core_engine as engine, ShardedSessionLocal as SessionLocal

# Declarative base class for models
Base = declarative_base()

# FastAPI Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

