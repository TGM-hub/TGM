"""
Database models and connection for encrypted HR data.

Stores encrypted employee records in a local SQLite database.
The raw values are never stored, only ciphertexts.
"""

from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///hr_encrypted.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Employee(Base):
    """
    Encrypted employee record.

    All sensitive fields (salary, age) are stored as ciphertexts.
    Department is stored as an encoded integer, not the original string.
    Name is hashed as we never compute on it, just identify records.
    """
    __tablename__ = "employees"

    id              = Column(Integer, primary_key=True, index=True)
    name  = Column(String)   # plaintext, client-side only
    name_hash       = Column(String)   # hashed — not decryptable
    department_code = Column(Integer)  # RH=1, IT=2, Finance=3
    encrypted_age    = Column(Float)   # age + key
    encrypted_salary = Column(Float)   # salary + key


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Return a new database session."""
    return SessionLocal()