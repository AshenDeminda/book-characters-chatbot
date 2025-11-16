"""
Document Management Service
Handles document metadata and status tracking

TASK 2: Background Job Processing
This service manages document status during async processing
"""
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import logging

from src.models.schemas import DocumentMetadata, DocumentStatus

logger = logging.getLogger(__name__)

class DocumentService:
    """Manages document metadata and status"""
    
    def __init__(self, storage_dir: str = "data/documents"):
        """
        Initialize document service
        
        Args:
            storage_dir: Directory to store document metadata
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_metadata_path(self, document_id: str) -> Path:
        """Get path to document metadata file"""
        return self.storage_dir / f"{document_id}_metadata.json"
    
    def create_document(
        self, 
        document_id: str, 
        filename: str, 
        file_size: int
    ) -> DocumentMetadata:
        """
        Create new document record
        
        Args:
            document_id: Unique document identifier
            filename: Original filename
            file_size: File size in bytes
            
        Returns:
            Document metadata
        """
        now = datetime.now()
        metadata = DocumentMetadata(
            document_id=document_id,
            filename=filename,
            file_size=file_size,
            status=DocumentStatus.UPLOADING,
            progress=0,
            message="File uploaded, starting processing...",
            created_at=now,
            updated_at=now
        )
        
        self._save_metadata(metadata)
        logger.info(f"Created document record: {document_id}")
        return metadata
    
    def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        progress: int,
        message: str,
        **kwargs
    ) -> Optional[DocumentMetadata]:
        """
        Update document processing status
        
        Args:
            document_id: Document identifier
            status: New status
            progress: Progress percentage (0-100)
            message: Status message
            **kwargs: Additional fields to update (page_count, chunk_count, error_message)
            
        Returns:
            Updated metadata or None if not found
        """
        metadata = self.get_document(document_id)
        if not metadata:
            logger.error(f"Document {document_id} not found for status update")
            return None
        
        # Update fields
        metadata.status = status
        metadata.progress = progress
        metadata.message = message
        metadata.updated_at = datetime.now()
        
        # Update optional fields
        for key, value in kwargs.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
        
        self._save_metadata(metadata)
        logger.info(f"Updated document {document_id}: {status.value} ({progress}%)")
        return metadata
    
    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """
        Get document metadata
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document metadata or None if not found
        """
        metadata_path = self._get_metadata_path(document_id)
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert string dates back to datetime
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            return DocumentMetadata(**data)
        except Exception as e:
            logger.error(f"Error loading document metadata: {e}")
            return None
    
    def list_documents(self) -> List[DocumentMetadata]:
        """
        List all documents
        
        Returns:
            List of document metadata
        """
        documents = []
        for metadata_file in self.storage_dir.glob("*_metadata.json"):
            document_id = metadata_file.stem.replace("_metadata", "")
            doc = self.get_document(document_id)
            if doc:
                documents.append(doc)
        
        # Sort by created_at descending (newest first)
        documents.sort(key=lambda x: x.created_at, reverse=True)
        return documents
    
    def _save_metadata(self, metadata: DocumentMetadata) -> None:
        """Save metadata to disk"""
        metadata_path = self._get_metadata_path(metadata.document_id)
        
        # Convert to dict and handle datetime serialization
        data = metadata.dict()
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
