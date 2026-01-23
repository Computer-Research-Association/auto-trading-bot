from __future__ import annotations
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from sqlalchemy.util import await_only

from app.domains.portfolio.schemas import PortfolioAssetsResponse
import app.domains.portfolio.service as service

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])
@router.get("/assets") #response_model=PortfolioAssetsResponse)
async def get_assets() -> PortfolioAssetsResponse:
    try:
        return await service.get_assets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
