import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Get PostgreSQL connection string from environment variables for core transactional DB
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ui_ai_db"
)

# Get connection string for analytics/logs DB (falls back to main DB)
ANALYTICS_DATABASE_URL = os.getenv(
    "ANALYTICS_DATABASE_URL",
    DATABASE_URL
)

# Configure sqlite threading args if SQLite is active
connect_args_core = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args_core = {"check_same_thread": False}

connect_args_analytics = {}
if ANALYTICS_DATABASE_URL.startswith("sqlite"):
    connect_args_analytics = {"check_same_thread": False}

# Instantiate distinct database engines
core_engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args_core)
analytics_engine = create_engine(ANALYTICS_DATABASE_URL, pool_pre_ping=True, connect_args=connect_args_analytics)


class RoutingSession(Session):
    """Dynamic routing SQLAlchemy session mapping queries/inserts to different engines.

    Queries or inserts targeting the 'Log' model are routed to the
    analytics_engine database, while all other models go to the core_engine.
    """

    def get_bind(self, mapper=None, clause=None):
        if mapper:
            # Check class name string to avoid circular dependency imports of models at runtime
            class_name = mapper.class_.__name__
            if class_name == "Log" or class_name == "TrainingHistory":
                return analytics_engine
        return core_engine


# Session local factory utilizing RoutingSession
ShardedSessionLocal = sessionmaker(
    class_=RoutingSession,
    autocommit=False,
    autoflush=False
)
