from fastapi import FastAPI
from . import experiments


def create_app() -> FastAPI:
    """
    Create a FastAPI application with the experiments router.
    """
    app = FastAPI()
    app.include_router(experiments.router)
    return app
