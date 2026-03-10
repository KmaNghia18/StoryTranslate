"""
StoryTranslate Backend - FastAPI Application
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.translate_router import router as translate_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    # Preload OCR model in background (downloads ~100MB first time)
    logger.info("Starting OCR model preload in background...")
    from app.services.ocr_service import preload_reader
    preload_reader(["en"])
    yield


app = FastAPI(
    title="StoryTranslate API",
    description="API for translating novel text and images",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Detections", "X-Detections-Count"],
)

# Include routers
app.include_router(translate_router)


@app.get("/")
async def root():
    return {
        "name": "StoryTranslate API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

