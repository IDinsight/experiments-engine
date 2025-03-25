from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

from . import auth, contextual_mab, mab, messages
from .config import REDIS_HOST
from .users.routers import (
    router as users_router,
)  # to avoid circular imports
from .utils import setup_logger

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan events for the FastAPI application.
    """

    logger.info("Application started")
    app.state.redis = await aioredis.from_url(REDIS_HOST)

    yield

    await app.state.redis.close()
    logger.info("Application finished")


def create_app() -> FastAPI:
    """
    Create a FastAPI application with the experiments router.
    """
    app = FastAPI(title="Experiments API", lifespan=lifespan)
    app.include_router(mab.router)
    app.include_router(contextual_mab.router)
    app.include_router(auth.router)
    app.include_router(users_router)
    app.include_router(messages.router)

    origins = [
        "http://localhost",
        "http://localhost:3000",
        "https://localhost",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
