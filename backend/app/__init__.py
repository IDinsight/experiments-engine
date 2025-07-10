from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import asyncio as aioredis

from . import auth, messages
from .ai_helpers.routers import router as ai_helpers_router
from .config import BACKEND_ROOT_PATH, DOMAIN, REDIS_HOST
from .experiments.routers import router as experiments_router
from .users.routers import (
    router as users_router,
)  # to avoid circular imports
from .utils import setup_logger
from .workspaces.routers import router as workspaces_router

logger = setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan events for the FastAPI application.
    """

    logger.info("Application started")
    app.state.redis = await aioredis.from_url(REDIS_HOST)

    yield

    await app.state.redis.aclose()
    logger.info("Application finished")


def create_app() -> FastAPI:
    """
    Create a FastAPI application with the experiments router.
    """
    app = FastAPI(
        title="Experiments API",
        lifespan=lifespan,
        openapi_prefix=BACKEND_ROOT_PATH,
    )

    origins = [
        f"http://{DOMAIN}",
        f"http://{DOMAIN}:3000",
        f"https://{DOMAIN}",
        f"https://{DOMAIN}:3000",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    app.include_router(experiments_router)
    app.include_router(auth.router)
    app.include_router(users_router)
    app.include_router(messages.router)
    app.include_router(workspaces_router)
    app.include_router(ai_helpers_router)

    return app
