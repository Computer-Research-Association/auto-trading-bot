from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.params import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

import core.cors as cors_config
from app.api.router import api_router
from core.deps import get_database
from core.logger import logger, setup_logging

from fastapi import  Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("lifespan started")



    yield
    logger.info("lifespan stopped")




app = FastAPI(lifespan=lifespan)


@app.get("/db-test")
async def db_test(db: AsyncSession = Depends(get_database)):
    result = await db.execute(text("SELECT 1"))
    value = result.scalar()
    return {"db": "ok", "result": value}



cors_config.setup_cors(app)
app.include_router(api_router)
