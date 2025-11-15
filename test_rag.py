"""
Test script for RAG (Vector Store) functionality
Usage: python test_rag.py <document_id>
"""
import sys
from src.rag.rag_service import RAGService

def test_rag_service(document_id: str):
    """Test RAG service and vector store"""
    print("="*80)
    print("🧠 RAG SERVICE TEST")
    print("="*80)
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Step 1: Check if document exists in vector store
    print(f"\n📝 Step 1: Checking if document exists...")
    print(f"Document ID: {document_id}")
    
    try:
        chunks = rag_service.get_document_chunks(document_id)
        
        if not chunks:
            print("❌ No chunks found for this document!")
            print("\nMake sure you've uploaded the document first:")
            print("  POST http://localhost:8000/api/v1/upload")
            return
        
        print(f"✅ Found {len(chunks)} chunks in vector store")
        
        # Show sample chunk
        if chunks:
            print(f"\n📄 Sample chunk:")
            print(f"   ID: {chunks[0]['id']}")
            print(f"   Text: {chunks[0]['text'][:200]}...")
            if chunks[0].get('metadata'):
                print(f"   Metadata: {chunks[0]['metadata']}")
        
    except Exception as e:
        print(f"❌ Error getting chunks: {e}")
        return
    
    # Step 2: Test context retrieval
    print("\n" + "="*80)
    print("🔍 Step 2: Testing context retrieval")
    print("="*80)
    
    test_queries = [
        "Who is the main character?",
        "What is the character's personality?",
        "What happened in the story?",
        "Tell me about the character's background",
        "What are the character's relationships?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: \"{query}\"")
        
        try:
            results = rag_service.search_relevant_context(
                query=query,
                document_id=document_id,
                n_results=3
            )
            
            print(f"✅ Found {len(results)} relevant chunks:")
            
            for i, result in enumerate(results, 1):
                relevance = result.get('relevance_score', 0)
                text = result.get('text', '')
                
                print(f"\n   {i}. Relevance: {relevance:.2%}")
                print(f"      Text: {text[:150]}...")
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            continue
    
    # Step 3: Statistics
    print("\n" + "="*80)
    print("📊 VECTOR STORE STATISTICS")
    print("="*80)
    print(f"Total chunks: {len(chunks)}")
    
    if chunks:
        total_chars = sum(len(chunk['text']) for chunk in chunks)
        avg_chars = total_chars / len(chunks)
        print(f"Total characters: {total_chars:,}")
        print(f"Average chunk size: {avg_chars:.0f} characters")
        
        # Check metadata
        has_metadata = any(chunk.get('metadata') for chunk in chunks)
        print(f"Has metadata: {'✅' if has_metadata else '❌'}")
    
    print("\n✅ RAG service is working correctly!")
    print(f"\n💡 You can now test the chat:")
    print(f"   python test_get_characters.py {document_id}")
    print(f"   python test_chat.py {document_id} <character_id>")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_rag.py <document_id>")
        print("\nExample:")
        print("  python test_rag.py fa0d116d-38ca-4de5-9f2b-611ddcde9d2f")
        sys.exit(1)
    
    document_id = sys.argv[1]
    test_rag_service(document_id)
