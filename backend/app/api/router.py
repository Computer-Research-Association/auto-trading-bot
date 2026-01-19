from fastapi import APIRouter

from app.domains.portfolio.routes import router as portfolio_router

api_router = APIRouter()
api_router.include_router(portfolio_router)
