"""
RAG Service for Book Characters Chatbot
Handles vector embeddings and retrieval for story context

PHASE 2 UPGRADE: Uses OpenAI embeddings for better retrieval accuracy
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pathlib import Path
from typing import List, Dict, Optional
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

from src.config import settings

logger = logging.getLogger(__name__)

class RAGService:
    """Manages vector embeddings and retrieval for story chunks"""
    
    def __init__(self, persist_directory: str = "chroma_db", batch_size: int = 20):
        """
        Initialize ChromaDB client and collection
        
        PHASE 2: Uses OpenAI embeddings if available, falls back to default
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            batch_size: Number of chunks to process in each batch (reduced to 20 for OpenAI token limits)
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.batch_size = batch_size  # Process chunks in batches for better performance
        
        # Initialize embedding function
        # PHASE 2: Use OpenAI embeddings for better quality
        self.embedding_function = None
        if settings.OPENAI_API_KEY:
            try:
                self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=settings.OPENAI_API_KEY,
                    model_name="text-embedding-3-small"  # Fast, high-quality, cost-effective
                )
                logger.info("Using OpenAI embeddings (text-embedding-3-small)")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
                logger.info("Falling back to default embeddings")
        else:
            logger.info("Using ChromaDB default embeddings (sentence-transformers)")
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection with embedding function
        self.collection_name = "story_chunks"
        
        # Check if collection exists - only recreate if dimensions actually mismatch
        try:
            existing_collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            self.collection = existing_collection
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except ValueError as e:
            # Dimension mismatch - need to recreate
            logger.warning(f"Collection dimension mismatch: {e}")
            logger.warning("Deleting old collection to use new OpenAI embeddings...")
            try:
                self.client.delete_collection(name=self.collection_name)
            except:
                pass
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=self.embedding_function
            )
            logger.info(f"Created new collection with OpenAI embeddings: {self.collection_name}")
        except Exception as e:
            # Collection doesn't exist - create it
            logger.info(f"Collection doesn't exist, creating: {e}")
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=self.embedding_function
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def add_document_chunks(
        self, 
        document_id: str, 
        chunks: List[str],
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Add document chunks to vector store
        
        TASK 1 OPTIMIZATION: Batch Processing
        - Processes chunks in batches to reduce overhead
        - ChromaDB handles internal parallelization for embeddings
        - Expected improvement: Better throughput for large documents
        
        Args:
            document_id: Unique identifier for the document
            chunks: List of text chunks
            metadata: Optional metadata for the document
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            logger.warning(f"No chunks provided for document {document_id}")
            return 0
        
        # Filter out chunks that are too large for OpenAI embeddings
        # OpenAI text-embedding-3-small has 8192 token limit PER CHUNK
        # Conservative estimate: 1 token ≈ 3 characters (safer than 4)
        # Limit to 2000 tokens per chunk to be very safe
        max_chars = 2000 * 3  # ~6,000 chars per chunk (2000 tokens)
        
        filtered_chunks = []
        for i, chunk in enumerate(chunks):
            if len(chunk) > max_chars:
                # Truncate oversized chunks instead of skipping
                filtered_chunks.append(chunk[:max_chars])
                logger.warning(f"Chunk {i} truncated from {len(chunk)} to {max_chars} chars")
            else:
                filtered_chunks.append(chunk)
        
        chunks = filtered_chunks
        
        # ==================================================================
        # NEW: BATCH PROCESSING (Task 1 Implementation)
        # Process chunks in batches for better performance with large documents
        # ==================================================================
        total_added = 0
        
        # Process chunks in batches
        for batch_start in range(0, len(chunks), self.batch_size):
            batch_end = min(batch_start + self.batch_size, len(chunks))
            batch_chunks = chunks[batch_start:batch_end]
            
            # Prepare data for this batch
            ids = [f"{document_id}_chunk_{i}" for i in range(batch_start, batch_end)]
            metadatas = []
            
            for i in range(batch_start, batch_end):
                chunk_metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "chunk_total": len(chunks)
                }
                if metadata:
                    chunk_metadata.update(metadata)
                metadatas.append(chunk_metadata)
            
            # Add batch to collection (ChromaDB handles embedding automatically)
            try:
                self.collection.add(
                    ids=ids,
                    documents=batch_chunks,
                    metadatas=metadatas
                )
                total_added += len(batch_chunks)
                logger.info(f"Added batch {batch_start//self.batch_size + 1}: {len(batch_chunks)} chunks")
            except Exception as e:
                logger.error(f"Error adding batch {batch_start//self.batch_size + 1}: {e}")
                raise
        
        logger.info(f"Total: Added {total_added} chunks for document {document_id}")
        return total_added
        
        # ==================================================================
        # OLD: SINGLE BATCH PROCESSING (Kept for reference)
        # Original implementation that processed all chunks at once
        # This could cause memory issues with very large documents
        # ==================================================================
        # ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        # metadatas = []
        # 
        # for i, chunk in enumerate(chunks):
        #     chunk_metadata = {
        #         "document_id": document_id,
        #         "chunk_index": i,
        #         "chunk_total": len(chunks)
        #     }
        #     if metadata:
        #         chunk_metadata.update(metadata)
        #     metadatas.append(chunk_metadata)
        # 
        # try:
        #     self.collection.add(
        #         ids=ids,
        #         documents=chunks,
        #         metadatas=metadatas
        #     )
        #     logger.info(f"Added {len(chunks)} chunks for document {document_id}")
        #     return len(chunks)
        # except Exception as e:
        #     logger.error(f"Error adding chunks to vector store: {e}")
        #     raise
    
    def search_relevant_context(
        self, 
        query: str, 
        document_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search for relevant chunks based on query
        
        Args:
            query: Search query
            document_id: Optional document ID to filter results
            n_results: Number of results to return
            
        Returns:
            List of relevant chunks with metadata and scores
        """
        try:
            # Build where clause for filtering
            where_clause = None
            if document_id:
                where_clause = {"document_id": document_id}
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            relevant_chunks = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    relevant_chunks.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'id': results['ids'][0][i] if results['ids'] else None
                    })
            
            logger.info(f"Found {len(relevant_chunks)} relevant chunks for query")
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            logger.warning(f"Returning empty results due to error. Document ID: {document_id}")
            return []
    
    def get_document_chunks(self, document_id: str) -> List[Dict]:
        """
        Get all chunks for a specific document
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of all chunks for the document
        """
        try:
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            chunks = []
            if results['documents']:
                for i, doc in enumerate(results['documents']):
                    chunks.append({
                        'text': doc,
                        'metadata': results['metadatas'][i] if results['metadatas'] else {},
                        'id': results['ids'][i] if results['ids'] else None
                    })
            
            logger.info(f"Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(
                where={"document_id": document_id}
            )
            logger.info(f"Deleted all chunks for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def collection_stats(self) -> Dict:
        """
        Get statistics about the collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "persist_directory": str(self.persist_directory)
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
