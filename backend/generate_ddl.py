import sys
import os

# Ensure the backend directory is in the python path for absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_mock_engine
from app.utills.models import Base

# Import all models to register them with Base.metadata
from models import User
from app.domains.log.models import OperatingLog
from app.domains.portfolio.models import PortfolioSnapshot

def dump(sql, *multiparams, **params):
    print(sql.compile(dialect=engine.dialect))

# Use a postgres dialect mock engine as the code uses JSONB (PostgreSQL specific)
engine = create_mock_engine("postgresql://", dump)

print("-- DDL Generated from SQLAlchemy Models")
print("-- This SQL can be used to manually create tables when Alembic is unavailable.\n")

# Generate DDL for all tables registered in Base.metadata
Base.metadata.create_all(engine)
