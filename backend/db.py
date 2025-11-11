from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
import os
DB_PATH = os.environ.get('APP_DB_PATH', '/data/app.db')
SQLITE_URL = f'sqlite:///{DB_PATH}'
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
def init_db():
    Base.metadata.create_all(bind=engine)
