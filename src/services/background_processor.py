"""
Background Document Processing
Handles async document processing tasks

TASK 2: Background Job Processing
This module processes documents asynchronously after upload returns to user
"""
import logging
from pathlib import Path

from src.utils.text_extractor import TextExtractor
from src.rag.rag_service import RAGService
from src.services.document_service import DocumentService
from src.models.schemas import DocumentStatus

logger = logging.getLogger(__name__)

def process_document_background(
    document_id: str,
    pdf_path: str,
    filename: str
):
    """
    Process uploaded document in background
    
    This function runs asynchronously after upload returns to user.
    Updates document status at each step so UI can poll for progress.
    
    Args:
        document_id: Unique document identifier
        pdf_path: Path to saved PDF file
        filename: Original filename
    """
    doc_service = DocumentService()
    text_extractor = TextExtractor()
    rag_service = RAGService()
    
    chunks_path = Path("data/uploads") / f"{document_id}_chunks.txt"
    
    try:
        # Step 1: Extract text from PDF
        logger.info(f"[BG] Starting text extraction for {document_id}")
        doc_service.update_status(
            document_id,
            DocumentStatus.EXTRACTING,
            20,
            "Extracting text from PDF..."
        )
        
        result = text_extractor.extract_from_pdf(pdf_path)
        
        logger.info(f"[BG] Extracted {result['page_count']} pages, {result['total_length']} chars")
        
        # Step 2: Create text chunks
        doc_service.update_status(
            document_id,
            DocumentStatus.CHUNKING,
            50,
            "Creating text chunks..."
        )
        
        # IMPROVED: Better chunk size for semantic coherence
        # 500 chars = ~100 words = better semantic units
        # 200 overlap = ensures context continuity
        chunks = text_extractor.chunk_text(
            result['full_text'],
            chunk_size=800,    # Smaller chunks = more precise retrieval
            overlap=200        # Larger overlap = better context preservation
        )
        
        logger.info(f"[BG] Created {len(chunks)} chunks")
        
        # Save chunks to file (for character extraction)
        with open(chunks_path, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(chunks):
                f.write(f"=== CHUNK {i+1} ===\n{chunk}\n\n")
        
        # Step 3: Index in ChromaDB
        doc_service.update_status(
            document_id,
            DocumentStatus.INDEXING,
            75,
            "Indexing in vector store..."
        )
        
        rag_service.add_document_chunks(
            document_id=document_id,
            chunks=chunks,
            metadata={
                "filename": filename,
                "page_count": result['page_count']
            }
        )
        
        logger.info(f"[BG] Indexed {len(chunks)} chunks in ChromaDB")
        
        # Step 4: Mark as ready
        doc_service.update_status(
            document_id,
            DocumentStatus.READY,
            100,
            "Document ready for character extraction and chat!",
            page_count=result['page_count'],
            chunk_count=len(chunks)
        )
        
        logger.info(f"[BG] Document {document_id} processing complete!")
        
    except Exception as e:
        logger.error(f"[BG] Error processing document {document_id}: {e}", exc_info=True)
        
        # Mark as failed
        doc_service.update_status(
            document_id,
            DocumentStatus.FAILED,
            0,
            "Processing failed",
            error_message=str(e)
        )
        
        # Cleanup on error
        try:
            if Path(pdf_path).exists():
                Path(pdf_path).unlink()
            if chunks_path.exists():
                chunks_path.unlink()
        except Exception as cleanup_error:
            logger.error(f"[BG] Cleanup error: {cleanup_error}")
