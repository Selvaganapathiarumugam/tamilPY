from app.logger import logger
from app.routes import api_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="{{PROJECT_NAME}}"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

logger.info("{{PROJECT_NAME}} application loaded")


@app.get("/health")
def health():
    logger.debug("Health check")
    return {"status": "ok"}
