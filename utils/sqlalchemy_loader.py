"""
sqlalchemy_loader.py
--------------------
SQLAlchemy ORM for loading Elizan III trial data from MySQL.

Recommended by Chadwick Boulay as a cleaner alternative to raw binary parsing
for animals where the MySQL server is accessible.

Usage:
    from utils.sqlalchemy_loader import get_engine, Trial
    engine = get_engine(host='localhost', db='elizan_db')
    
    with Session(engine) as session:
        trials = session.query(Trial).filter(Trial.phase == 1).all()
"""

from sqlalchemy import create_engine, Column, Integer, Float, LargeBinary, String
from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


class Trial(Base):
    """Maps to the Elizan III trial table."""
    __tablename__ = "trials"

    id           = Column(Integer, primary_key=True)
    animal_id    = Column(Integer)
    trial_number = Column(Integer)
    phase        = Column(Integer)   # 0=Baseline, 1=Down-cond1, etc.
    h_reflex_amp = Column(Float)     # H-reflex amplitude in µV
    m_wave_amp   = Column(Float)     # M-wave amplitude in µV
    timestamp    = Column(Integer)   # Unix timestamp (10-digit)
    signal_blob  = Column(LargeBinary)  # raw frag1 bytes


def get_engine(host: str, db: str, user: str = "root", password: str = ""):
    """Create SQLAlchemy engine for Elizan III MySQL database."""
    url = f"mysql+pymysql://{user}:{password}@{host}/{db}"
    return create_engine(url, echo=False)


def load_trials_to_numpy(session, animal_id: int, phase: int = None):
    """
    Load trial signal blobs and decode to numpy arrays.
    
    TODO: implement full blob → numpy decoding using decoder_2013 / decoder_2006 logic.
    """
    import numpy as np

    query = session.query(Trial).filter(Trial.animal_id == animal_id)
    if phase is not None:
        query = query.filter(Trial.phase == phase)

    trials = query.all()
    # TODO: decode signal_blob → numpy array for each trial
    raise NotImplementedError("Blob decoding not yet implemented — see decoder_2013.py for format details")
