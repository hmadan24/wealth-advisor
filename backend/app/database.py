"""
Database configuration and models using SQLAlchemy.
Supports both SQLite (local dev) and PostgreSQL (Supabase/production).
"""
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.mutable import MutableDict
from datetime import datetime
import json
import os

from app.config import settings

# Configure database URL
DATABASE_URL = settings.DATABASE_URL

# Fix for Supabase/Heroku postgres:// URLs (SQLAlchemy 1.4+ requires postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False, PostgreSQL doesn't need it
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class JSONEncodedDict(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


# Use MutableDict to track changes to JSON
MutableJSONDict = MutableDict.as_mutable(JSONEncodedDict)


class User(Base):
    """User model - stores user info linked to phone number."""
    __tablename__ = "users"
    
    phone = Column(String(15), primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    supabase_uid = Column(String(255), nullable=True, index=True)  # Supabase user ID
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Portfolio(Base):
    """Portfolio model - stores parsed CAS data per user."""
    __tablename__ = "portfolios"
    
    id = Column(String(36), primary_key=True)  # UUID
    phone = Column(String(15), index=True)
    filename = Column(String(255))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    portfolio_data = Column(MutableJSONDict)  # Stores the full parsed portfolio with mutation tracking
    

# Create tables
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    """Get database session - use as FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
