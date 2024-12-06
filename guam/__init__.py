import uvicorn
from fastapi import FastAPI

from guam import router


def main():
    app = FastAPI()

    app.include_router(router.router)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
