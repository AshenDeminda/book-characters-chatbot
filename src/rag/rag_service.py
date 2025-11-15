"""
RAG Service for Book Characters Chatbot
Handles vector embeddings and retrieval for story context
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Optional
import logging
import uuid

logger = logging.getLogger(__name__)

class RAGService:
    """Manages vector embeddings and retrieval for story chunks"""
    
    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Initialize ChromaDB client and collection
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection_name = "story_chunks"
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
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
        
        # Prepare data for ChromaDB
        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "document_id": document_id,
                "chunk_index": i,
                "chunk_total": len(chunks)
            }
            if metadata:
                chunk_metadata.update(metadata)
            metadatas.append(chunk_metadata)
        
        # Add to collection (ChromaDB handles embedding automatically)
        try:
            self.collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas
            )
            logger.info(f"Added {len(chunks)} chunks for document {document_id}")
            return len(chunks)
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            raise
    
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
