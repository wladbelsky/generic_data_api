import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database.logging.request_log import Base


class Database:
    def __init__(self, clickhouse_url: str = None):
        if clickhouse_url is None:
            clickhouse_url = os.getenv('CLICKHOUSE_URL', 'clickhouse://default:@clickhouse:9000/logs')
        self.engine = create_engine(clickhouse_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables if they don't exist"""
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


def get_database() -> Database:
    """Dependency injection function for Database"""
    return Database()
