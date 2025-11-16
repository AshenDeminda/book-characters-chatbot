from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from pathlib import Path
import uuid
import os

from src.services.document_service import DocumentService
from src.services.background_processor import process_document_background
from src.models.schemas import DocumentStatusResponse, DocumentStatus
from src.config import settings

router = APIRouter()
doc_service = DocumentService()


# ==================================================================
# TASK 2: Background Job Processing - Async Upload Endpoint
# ==================================================================

@router.post("/upload")
async def upload_storybook(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a PDF storybook for processing
    
    TASK 2 OPTIMIZATION: Background Job Processing
    - Returns immediately after saving file (< 2 seconds)
    - Processing happens in background
    - Use GET /api/v1/documents/{document_id}/status to check progress
    - Expected UX improvement: 95% reduction in perceived latency
    """
    # Validate PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Check file size
    content = await file.read()
    file_size = len(content)
    
    max_size = getattr(settings, 'MAX_FILE_SIZE', 100 * 1024 * 1024)  # 100MB default
    if file_size > max_size:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size: {max_size / 1024 / 1024}MB"
        )
    
    if file_size < 1024:  # Less than 1KB
        raise HTTPException(status_code=400, detail="File too small or empty")
    
    # Generate unique ID
    document_id = str(uuid.uuid4())
    
    # Create upload directory
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save PDF
    pdf_path = upload_dir / f"{document_id}.pdf"
    
    try:
        # Save uploaded file
        with open(pdf_path, 'wb') as f:
            f.write(content)
        
        # Create document record
        doc_service.create_document(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size
        )
        
        # Queue background processing
        background_tasks.add_task(
            process_document_background,
            document_id=document_id,
            pdf_path=str(pdf_path),
            filename=file.filename
        )
        
        return {
            "status": "processing",
            "document_id": document_id,
            "filename": file.filename,
            "file_size": file_size,
            "message": "Upload successful! Processing started in background.",
            "status_url": f"/api/v1/documents/{document_id}/status"
        }
    
    except Exception as e:
        # Cleanup on error
        if pdf_path.exists():
            os.remove(pdf_path)
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str):
    """
    Get document processing status
    
    Poll this endpoint to check if document is ready.
    Frontend should poll every 1-2 seconds until status is 'ready' or 'failed'.
    """
    metadata = doc_service.get_document(document_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentStatusResponse(
        document_id=metadata.document_id,
        filename=metadata.filename,
        status=metadata.status,
        progress=metadata.progress,
        message=metadata.message,
        page_count=metadata.page_count,
        chunk_count=metadata.chunk_count,
        created_at=metadata.created_at,
        is_ready=(metadata.status == DocumentStatus.READY),
        error_message=metadata.error_message
    )


@router.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    documents = doc_service.list_documents()
    
    return {
        "total": len(documents),
        "documents": [
            {
                "document_id": doc.document_id,
                "filename": doc.filename,
                "status": doc.status,
                "progress": doc.progress,
                "created_at": doc.created_at.isoformat(),
                "is_ready": (doc.status == DocumentStatus.READY)
            }
            for doc in documents
        ]
    }


# ==================================================================
# OLD SYNCHRONOUS UPLOAD (Kept for reference - Task 2)
# ==================================================================
# @router.post("/upload")
# async def upload_storybook(file: UploadFile = File(...)):
#     # ... old blocking implementation (see git history)