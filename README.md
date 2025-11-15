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

- **POST /api/v1/upload** - Upload PDF book
- **POST /api/v1/characters/extract-characters** - Extract characters
- **GET /api/v1/characters/extract-characters/{document_id}** - Get cached characters
- **POST /api/v1/chat** - Chat with character
- **POST /api/v1/chat/greeting** - Get character greeting