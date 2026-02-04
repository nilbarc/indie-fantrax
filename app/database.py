import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    submitter_name = Column(String(100), nullable=False)
    album_title = Column(String(255))
    artist_name = Column(String(255))
    context = Column(Text)
    spotify_url = Column(String(500))
    apple_music_url = Column(String(500))
    songlink_url = Column(String(500))
    album_art_url = Column(String(500))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    posted_at = Column(DateTime, nullable=True)
    is_posted = Column(Boolean, default=False)
    post_number = Column(Integer, nullable=True)


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id = Column(Integer, primary_key=True, index=True)
    is_paused = Column(Boolean, default=False)
    paused_at = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)
    _run_migrations()


def _run_migrations():
    """Run database migrations for new columns."""
    with engine.connect() as conn:
        # Check if post_number column exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'recommendations' AND column_name = 'post_number'
        """))
        if result.fetchone() is None:
            logger.info("Adding post_number column to recommendations table")
            conn.execute(text("ALTER TABLE recommendations ADD COLUMN post_number INTEGER"))
            conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
