from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_database
from app.domains.portfolio.schemas import PortfolioAssetsResponse
from app.domains.portfolio.service import get_assets as get_assets_service
from app.domains.portfolio.service import take_portfolio_snapshot

router = APIRouter()

@router.get("/assets", response_model=PortfolioAssetsResponse)
def get_assets_route():
    return get_assets_service()


@router.post("/snapshot")
def create_snapshot(db = Depends(get_database)):
    return take_portfolio_snapshot(db, base_date=date.today())