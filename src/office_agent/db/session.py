from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from office_agent.config import settings
from office_agent.db.models import Base

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
def create_schema() -> None: Base.metadata.create_all(engine)
def get_session() -> Session: return SessionLocal()
