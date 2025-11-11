from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    APP_NAME: str = "Book Characters Chatbot API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # AI Configuration
    # OpenAI Configuration 
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Gemini Configuration 
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "models/gemini-2.5-flash"
    
    # Which AI provider to use: "openai" or "gemini"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")

    # Vector Database
    VECTOR_DB_TYPE: str = "chroma"
    VECTOR_DB_PATH: str = "./data/vectors"

    # File Upload
    UPLOAD_DIR: str = "./data/uploads"
    MAX_FILE_SIZE: int = 52428800  # 50 MB

    # NLP Configuration
    SPACY_MODEL: str = "en_core_web_sm"
    MIN_CHARACTER_MENTIONS: int = 5

    # Session Management
    SESSION_TIMEOUT: int = 3600  # 1 hour

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()