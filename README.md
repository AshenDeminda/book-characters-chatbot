# Book Characters Chatbot

RAG application that lets users chat with book characters based on uploaded books.

## Features
- ✅ Upload books (PDF)
- ✅ Automatic text extraction and chunking
- ✅ AI-powered character name extraction
- ✅ Entity resolution (merges character aliases)
- ✅ Character personality/behavior analysis
- ✅ Character caching for fast responses
- ✅ RAG-powered character chat
- ✅ Chat history persistence (all books)
- ✅ Default books with preloaded characters
- ✅ FastAPI REST API with interactive docs

## Tech Stack
- FastAPI
- LangChain
- Google Gemini AI
- ChromaDB (Vector Store)
- SQLite

## Setup

1. **Create virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
Create `.env` file with:
```
GEMINI_API_KEY=your_key_here
```

4. **Start server:**
```bash
python run.py
```

5. **Open API docs:**
Navigate to `http://localhost:8000/docs`

## API Endpoints

### Upload & Characters
- **POST /api/v1/upload** - Upload PDF book
- **POST /api/v1/characters/extract-characters** - Extract characters
- **GET /api/v1/characters/extract-characters/{document_id}** - Get cached characters

### Default Books
- **GET /api/v1/default-books** - List all default books
- **GET /api/v1/default-books/{book_id}/characters** - Get preloaded characters

### Chat
- **POST /api/v1/chat** - Chat with character (non-streaming)
- **POST /api/v1/chat/stream** - Chat with character (streaming)
- **POST /api/v1/chat/greeting** - Get character greeting

### Chat History (Works for all books)
- **GET /api/v1/chat/session/history** - Load conversation history
- **POST /api/v1/chat/session/save** - Save chat message
- **DELETE /api/v1/chat/session/clear** - Clear conversation history