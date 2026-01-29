from contextlib import asynccontextmanager

from fastapi import FastAPI

import core.cors as cors_config
from app.api.router import api_router
from core.logger import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("lifespan started")
    yield
    logger.info("lifespan stopped")
app = FastAPI(lifespan=lifespan)

cors_config.setup_cors(app)
app.include_router(api_router)
