# Book Characters Chatbot

RAG application that lets users chat with book characters based on uploaded books.

## Features
- ✅ Upload books (PDF)
- ✅ Automatic text extraction and chunking
- ✅ AI-powered character name extraction
- ✅ Entity resolution (merges character aliases)
- ✅ Character personality/behavior analysis
- 🚧 Character-based chatbot (coming soon)
- 🚧 RAG for context-aware conversations (coming soon)

## Tech Stack
- FastAPI
- LangChain
- PostgreSQL/SQLite
- Vector Database (ChromaDB/FAISS)

## Setup
Coming soon...
```

---


# Start server
python run.py

# Test upload
python test_upload.py "path\to\your\file.pdf"

# Test character extraction (names only)
python test_characters.py <document_id>

# Test character extraction with personality analysis
python test_personality.py <document_id>

# Test entity resolution (alias merging)
python test_entity_resolution.py <document_id>




venv\Scripts\activate