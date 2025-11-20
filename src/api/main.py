from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from src.config import settings
from src.api.routes import upload, characters, chat, default_books, default_movies
from src.models.database import Base, engine
from src.models.chat_session import ChatSession  # Import to register model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    logger.info("Starting up...")
    
    # Create necessary directories
    directories = [
        Path("data/uploads"),
        Path("data/cache"),
        Path("data/documents"),
        Path("data/character_profiles"),
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    logger.info("Created data directories")
    
    # Initialize database
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
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(default_books.router, prefix="/api/v1", tags=["Default Books"])
app.include_router(default_movies.router, prefix="/api/v1", tags=["Default Movies"])

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
    """Serve the main UI"""
    static_dir = Path(__file__).parent.parent.parent / "static"
    index_file = static_dir / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    
    return {
        "message": "Book Characters Chatbot API",
        "version": settings.VERSION,
        "docs": "/docs",
        "ui": "UI not found. Please create static/index.html"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
