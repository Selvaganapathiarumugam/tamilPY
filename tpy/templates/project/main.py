from fastapi import FastAPI

from app.logger import logger
from app.routes import api_router

app = FastAPI(
    title="{{PROJECT_NAME}}"
)

app.include_router(api_router)

logger.info("{{PROJECT_NAME}} application loaded")


@app.get("/health")
def health():
    logger.debug("Health check")
    return {"status": "ok"}
