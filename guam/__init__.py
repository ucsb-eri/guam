import uvicorn
from fastapi import FastAPI

from guam import router
from guam.config import config


def main():
    app = FastAPI()

    app.include_router(router.router)

    server_config = config.get("server", {})

    uvicorn.run(
        app,
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        log_level=server_config.get("log_level", "info"),
    )
