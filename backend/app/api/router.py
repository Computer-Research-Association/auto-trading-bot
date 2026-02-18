from fastapi import APIRouter

from app.domains.portfolio.routes import router as portfolio_router
from app.domains.performance.routes import router as performance_router
from app.domains.log.routes import router as log_router
from app.domains.log.routes import router as log_router

api_router = APIRouter(prefix="/api")

api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(performance_router, tags=["performance"])
api_router.include_router(log_router)
api_router.include_router(log_router)