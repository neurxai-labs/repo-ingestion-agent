import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Base
logger = logging.getLogger(__name__)
class Database:
    def __init__(self, db_url: str = settings.DATABASE_URL):
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.setup_wal_mode()
    def setup_wal_mode(self):
        """
        Sets up WAL mode for the SQLite database.
        """
        if self.engine.dialect.name == "sqlite":
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                try:
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    logger.info("WAL mode enabled for SQLite")
                finally:
                    cursor.close()
    def get_db(self):
        """
        Returns a new database session.
        """
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    def init_db(self):
        """
        Initializes the database and creates all tables.
        """
        Base.metadata.create_all(bind=self.engine)
db = Database()
