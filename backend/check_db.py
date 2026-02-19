import asyncio
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Load .env explicitly
load_dotenv(BASE_DIR / ".env")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
from app.domains.portfolio.models import PortfolioSnapshot
from app.domains.portfolio.service import take_portfolio_snapshot
from app.database import get_session

# Override host to localhost for running from host machine
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("@db:", "@localhost:")

if not DATABASE_URL:
    print("DATABASE_URL not found!")
    sys.exit(1)

# Ensure async driver is used
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

print(f"Connecting to: {DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check_snapshots():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PortfolioSnapshot).order_by(PortfolioSnapshot.base_date.desc()).limit(10)
        )
        snaps = result.scalars().all()
        
        print(f"\n--- Current Snapshots ({len(snaps)}) ---")
        for s in snaps:
            print(f"Date: {s.base_date} | Equity: {s.equity_krw:,.0f} | PnL: {s.pnl_krw:,.0f} | Rate: {s.pnl_rate:.2f}%")
        print("-----------------------------------")

async def delete_snapshots():
    async with AsyncSessionLocal() as session:
        print("\nDeleting all snapshots...")
        await session.execute(delete(PortfolioSnapshot))
        await session.commit()
        print("All snapshots deleted.")

# Sync function to create snapshot (service uses sync session for some reason? No, it uses Session but we have AsyncSession here)
# Wait, take_portfolio_snapshot takes a Sync Session (sqlalchemy.orm.Session), not AsyncSession.
# database.py has get_session() which yields Session(engine). But engine in database.py is sync engine.
# So we need to import engine from database.py and use it.

def create_snapshot_sync():
    print("\nCreating new snapshot from Upbit...")
    # We need to use valid DB connection for the service function
    # The service function expects a Sync Session.
    # We should setup a sync engine for this.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    
    SYNC_DB_URL = os.getenv("DATABASE_URL", "").replace("@db:", "@localhost:")
    # Remove +asyncpg if present (though env usually has psycopg2 or nothing)
    # The Env has postgresql+psycopg2, which is sync.
    
    sync_engine = create_engine(SYNC_DB_URL)
    with Session(sync_engine) as session:
        from datetime import date
        try:
            snap = take_portfolio_snapshot(session, date.today())
            print(f"Snapshot created! Date: {snap.base_date}, Equity: {snap.equity_krw:,.0f} KRW")
        except Exception as e:
            print(f"Error creating snapshot: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true", help="Delete all snapshots")
    parser.add_argument("--create", action="store_true", help="Create a new snapshot")
    args = parser.parse_args()

    if args.delete:
        asyncio.run(delete_snapshots())
    
    if args.create:
        create_snapshot_sync()
        
    asyncio.run(check_snapshots())
