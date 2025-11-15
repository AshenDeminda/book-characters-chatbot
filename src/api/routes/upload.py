from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import uuid
import os

from src.utils.text_extractor import TextExtractor
from src.rag.rag_service import RAGService
from src.config import settings

router = APIRouter()
text_extractor = TextExtractor()
rag_service = RAGService()

@router.post("/upload")
async def upload_storybook(file: UploadFile = File(...)):
    """
    Upload a PDF storybook and extract text
    """
    # Validate PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Generate unique ID
    document_id = str(uuid.uuid4())
    
    # Create upload directory
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save PDF
    pdf_path = upload_dir / f"{document_id}.pdf"
    
    try:
        content = await file.read()
        with open(pdf_path, 'wb') as f:
            f.write(content)
        
        # Extract text
        result = text_extractor.extract_from_pdf(str(pdf_path))
        
        # Create text chunks
        chunks = text_extractor.chunk_text(
            result['full_text'],
            chunk_size=1000,
            overlap=100
        )
        
        # Save only chunks (no need for full text file)
        chunks_path = upload_dir / f"{document_id}_chunks.txt"
        with open(chunks_path, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(chunks):
                f.write(f"=== CHUNK {i+1} ===\n{chunk}\n\n")
        
        # Add chunks to vector store for RAG
        rag_service.add_document_chunks(
            document_id=document_id,
            chunks=chunks,
            metadata={
                "filename": file.filename,
                "page_count": result['page_count']
            }
        )
        
        return {
            "status": "success",
            "document_id": document_id,
            "filename": file.filename,
            "page_count": result['page_count'],
            "text_length": result['total_length'],
            "chunks_count": len(chunks),
            "message": "Storybook processed and indexed for RAG"
        }
    
    except Exception as e:
        # Cleanup on error
        if pdf_path.exists():
            os.remove(pdf_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")