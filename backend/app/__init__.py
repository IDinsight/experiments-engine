from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import mab


def create_app() -> FastAPI:
    """
    Create a FastAPI application with the experiments router.
    """
    app = FastAPI()
    app.include_router(mab.router)

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
