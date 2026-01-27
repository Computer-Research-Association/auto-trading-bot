from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.api.deps import get_session
from app.domains.portfolio.schemas import PortfolioAssetsResponse
from app.domains.portfolio.service import get_assets as get_assets_service
from app.domains.portfolio.service import take_portfolio_snapshot

router = APIRouter()

@router.get("/assets", response_model=PortfolioAssetsResponse)
def get_assets_route():
    return get_assets_service()


@router.post("/snapshot")
def create_snapshot(session: Session = Depends(get_session)):
    return take_portfolio_snapshot(session, base_date=date.today())