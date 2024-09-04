from fastapi import FastAPI
from . import mab


def create_app() -> FastAPI:
    """
    Create a FastAPI application with the experiments router.
    """
    app = FastAPI()
    app.include_router(mab.router)
    return app
