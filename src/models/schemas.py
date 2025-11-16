from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from .database import Base
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    file_path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer)
    name = Column(String, index=True)
    description = Column(Text)
    traits = Column(Text)


# ==================================================================
# TASK 2: Background Job Processing - Document Status Models
# ==================================================================

class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    EXTRACTING = "extracting_text"
    CHUNKING = "chunking"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"

class DocumentMetadata(BaseModel):
    """Document metadata stored in database"""
    document_id: str
    filename: str
    file_size: int
    status: DocumentStatus
    progress: int = 0  # 0-100
    message: str = ""
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

class DocumentStatusResponse(BaseModel):
    """Response for status endpoint"""
    document_id: str
    filename: str
    status: DocumentStatus
    progress: int
    message: str
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: datetime
    is_ready: bool
    error_message: Optional[str] = None