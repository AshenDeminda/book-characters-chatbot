from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from src.config import settings
from src.api.routes import upload, characters
from src.models.database import Base, engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    logger.info("Starting up...")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down...")

# Initialize FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="RAG-based Book Characters Chatbot",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(characters.router, prefix="/api/v1", tags=["Characters"])

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc)
        }
    )

@app.get("/")
def root():
    return {
        "message": "Book Characters Chatbot API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
