# Book Characters Chatbot - API Documentation

Complete API reference for frontend integration with Vite + React.

---

## Base Configuration

**API Base URL:**
```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

**CORS:** Enabled for all origins (development)

---

## Endpoints

### 1. Upload PDF Book

Upload a PDF book for processing and character extraction.

**Endpoint:** `POST /upload`

**Content-Type:** `multipart/form-data`

**Request (React Example):**
```jsx
const uploadBook = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Upload failed:', error);
    throw error;
  }
};
```

**Response:**
```json
{
  "status": "success",
  "document_id": "d6bb236e-73a1-47a9-a906-a4a439f3bd3f",
  "filename": "solo_leveling_vol1.pdf",
  "page_count": 385,
  "text_length": 245678,
  "chunks_count": 245,
  "rag_indexed": true,
  "message": "Storybook processed and indexed for RAG"
}
```

**Error Response:**
```json
{
  "detail": "Only PDF files allowed"
}
```

---

### 2. Extract Characters (POST)

Extract characters from an uploaded book using AI.

**Endpoint:** `POST /characters/extract-characters`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "document_id": "d6bb236e-73a1-47a9-a906-a4a439f3bd3f",
  "max_characters": 10,
  "include_personality": false
}
```

**React Example:**
```jsx
const extractCharacters = async (documentId, maxCharacters = 10, includePersonality = false) => {
  try {
    const response = await fetch(`${API_BASE_URL}/characters/extract-characters`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        document_id: documentId,
        max_characters: maxCharacters,
        include_personality: includePersonality
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Character extraction failed:', error);
    throw error;
  }
};
```

**Response:**
```json
{
  "status": "success",
  "document_id": "d6bb236e-73a1-47a9-a906-a4a439f3bd3f",
  "characters": [
    {
      "character_id": "char_sung_jinwoo",
      "name": "Sung Jinwoo",
      "aliases": ["Jinwoo", "Sung Jinwoo", "Sung"],
      "description": "An E-rank hunter known as the weakest",
      "role": "protagonist",
      "personality": null
    }
  ],
  "total_found": 2,
  "from_cache": false
}
```

---

### 3. Get Characters (GET - Cached)

Retrieve previously extracted characters (uses cache).

**Endpoint:** `GET /characters/extract-characters/{document_id}`

**Query Parameters:**
- `include_personality` (boolean, default: true)
- `force_refresh` (boolean, default: false) - Bypass cache and re-extract

**React Example:**
```jsx
const getCharacters = async (documentId, includePersonality = true, forceRefresh = false) => {
  try {
    const params = new URLSearchParams({
      include_personality: includePersonality,
      force_refresh: forceRefresh
    });
    
    const response = await fetch(
      `${API_BASE_URL}/characters/extract-characters/${documentId}?${params}`
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Get characters failed:', error);
    throw error;
  }
};
```

**Response:** Same as POST version

---

### 4. Get Character Greeting

Get an initial greeting from a character.

**Endpoint:** `POST /chat/greeting`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "document_id": "d6bb236e-73a1-47a9-a906-a4a439f3bd3f",
  "character_id": "char_sung_jinwoo"
}
```

**React Example:**
```jsx
const getCharacterGreeting = async (documentId, characterId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat/greeting`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        document_id: documentId,
        character_id: characterId
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Get greeting failed:', error);
    throw error;
  }
};
```

**Response:**
```json
{
  "status": "success",
  "character_name": "Sung Jinwoo",
  "greeting": "I'm Sung Jinwoo, an E-rank hunter. What brings you here?"
}
```

---

### 5. Chat with Character

Send a message and get a character's response.

**Endpoint:** `POST /chat`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "document_id": "d6bb236e-73a1-47a9-a906-a4a439f3bd3f",
  "character_id": "char_sung_jinwoo",
  "message": "Tell me about your daily quests",
  "conversation_history": [
    {
      "role": "user",
      "content": "Hello!"
    },
    {
      "role": "assistant",
      "content": "I'm Sung Jinwoo. What would you like to know?"
    }
  ]
}
```

**React Example:**
```jsx
const chatWithCharacter = async (documentId, characterId, message, conversationHistory = []) => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        document_id: documentId,
        character_id: characterId,
        message: message,
        conversation_history: conversationHistory
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Chat failed:', error);
    throw error;
  }
};
```

**Response:**
```json
{
  "status": "success",
  "character_name": "Sung Jinwoo",
  "response": "The daily quests... they're mysterious. Every day I receive new tasks that I must complete. It's strange, but they've been helping me grow stronger.",
  "context_chunks_used": 5,
  "relevant_context": [
    {
      "text": "Jinwoo looked at the quest window floating before him. Today's quest was simple: 100 push-ups, 100 sit-ups...",
      "relevance_score": 0.87
    }
  ]
}
```

---

## TypeScript Types

Create `src/types/api.ts`:

```typescript
// API Response Types
export interface UploadResponse {
  status: string;
  document_id: string;
  filename: string;
  page_count: number;
  text_length: number;
  chunks_count: number;
  rag_indexed: boolean;
  message: string;
}

export interface Character {
  character_id: string;
  name: string;
  aliases: string[];
  description: string;
  role: 'protagonist' | 'supporting' | 'antagonist';
  personality?: {
    personality_traits: string[];
    behavior_summary: string;
    motivations: string;
    character_arc: string;
    defining_moments: string[];
  } | null;
}

export interface ExtractCharactersResponse {
  status: string;
  document_id: string;
  characters: Character[];
  total_found: number;
  from_cache: boolean;
}

export interface GreetingResponse {
  status: string;
  character_name: string;
  greeting: string;
}

export interface ConversationTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  status: string;
  character_name: string;
  response: string;
  context_chunks_used: number;
  relevant_context: Array<{
    text: string;
    relevance_score: number | null;
  }>;
}

export interface ErrorResponse {
  detail: string;
}
```

---

## React API Service

Create `src/services/api.ts`:

```typescript
import type {
  UploadResponse,
  ExtractCharactersResponse,
  GreetingResponse,
  ChatResponse,
  ConversationTurn
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  // Upload PDF
  async uploadBook(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }
    
    return response.json();
  }
  
  // Extract characters (POST)
  async extractCharacters(
    documentId: string,
    maxCharacters: number = 10,
    includePersonality: boolean = false
  ): Promise<ExtractCharactersResponse> {
    const response = await fetch(`${API_BASE_URL}/characters/extract-characters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: documentId,
        max_characters: maxCharacters,
        include_personality: includePersonality
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Character extraction failed');
    }
    
    return response.json();
  }
  
  // Get characters (GET - cached)
  async getCharacters(
    documentId: string,
    includePersonality: boolean = true,
    forceRefresh: boolean = false
  ): Promise<ExtractCharactersResponse> {
    const params = new URLSearchParams({
      include_personality: String(includePersonality),
      force_refresh: String(forceRefresh)
    });
    
    const response = await fetch(
      `${API_BASE_URL}/characters/extract-characters/${documentId}?${params}`
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get characters');
    }
    
    return response.json();
  }
  
  // Get character greeting
  async getGreeting(documentId: string, characterId: string): Promise<GreetingResponse> {
    const response = await fetch(`${API_BASE_URL}/chat/greeting`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: documentId,
        character_id: characterId
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get greeting');
    }
    
    return response.json();
  }
  
  // Chat with character
  async chat(
    documentId: string,
    characterId: string,
    message: string,
    conversationHistory: ConversationTurn[] = []
  ): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: documentId,
        character_id: characterId,
        message: message,
        conversation_history: conversationHistory
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat failed');
    }
    
    return response.json();
  }
}

export const apiService = new ApiService();
```

---

## React Hook Example

Create `src/hooks/useChat.ts`:

```typescript
import { useState } from 'react';
import { apiService } from '../services/api';
import type { ConversationTurn, ChatResponse } from '../types/api';

export const useChat = (documentId: string, characterId: string) => {
  const [conversationHistory, setConversationHistory] = useState<ConversationTurn[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const sendMessage = async (message: string): Promise<ChatResponse | null> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiService.chat(
        documentId,
        characterId,
        message,
        conversationHistory
      );
      
      // Update conversation history
      setConversationHistory(prev => [
        ...prev,
        { role: 'user', content: message },
        { role: 'assistant', content: response.response }
      ]);
      
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  };
  
  const clearHistory = () => {
    setConversationHistory([]);
  };
  
  return {
    conversationHistory,
    isLoading,
    error,
    sendMessage,
    clearHistory
  };
};
```

---

## Environment Setup

Create `.env` file in your Vite project root:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Complete React Component Example

```tsx
import { useState } from 'react';
import { apiService } from './services/api';
import { useChat } from './hooks/useChat';
import type { Character } from './types/api';

function App() {
  const [documentId, setDocumentId] = useState<string>('');
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null);
  const [greeting, setGreeting] = useState<string>('');
  
  const { conversationHistory, isLoading, error, sendMessage } = useChat(
    documentId,
    selectedCharacter?.character_id || ''
  );
  
  // Upload book
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    try {
      const result = await apiService.uploadBook(file);
      setDocumentId(result.document_id);
      alert('Book uploaded successfully!');
    } catch (err) {
      alert('Upload failed: ' + (err as Error).message);
    }
  };
  
  // Extract characters
  const handleExtractCharacters = async () => {
    if (!documentId) return;
    
    try {
      const result = await apiService.extractCharacters(documentId, 10, false);
      setCharacters(result.characters);
    } catch (err) {
      alert('Character extraction failed: ' + (err as Error).message);
    }
  };
  
  // Select character and get greeting
  const handleSelectCharacter = async (character: Character) => {
    setSelectedCharacter(character);
    
    try {
      const result = await apiService.getGreeting(documentId, character.character_id);
      setGreeting(result.greeting);
    } catch (err) {
      alert('Failed to get greeting: ' + (err as Error).message);
    }
  };
  
  // Send chat message
  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;
    await sendMessage(message);
  };
  
  return (
    <div className="app">
      <h1>Book Characters Chatbot</h1>
      
      {/* Upload Section */}
      <div className="upload-section">
        <input type="file" accept=".pdf" onChange={handleUpload} />
      </div>
      
      {/* Extract Characters */}
      {documentId && (
        <button onClick={handleExtractCharacters}>Extract Characters</button>
      )}
      
      {/* Characters List */}
      {characters.length > 0 && (
        <div className="characters-list">
          <h2>Characters</h2>
          {characters.map(char => (
            <div key={char.character_id} onClick={() => handleSelectCharacter(char)}>
              <h3>{char.name}</h3>
              <p>{char.description}</p>
            </div>
          ))}
        </div>
      )}
      
      {/* Chat Interface */}
      {selectedCharacter && (
        <div className="chat-interface">
          <h2>Chat with {selectedCharacter.name}</h2>
          <p className="greeting">{greeting}</p>
          
          <div className="messages">
            {conversationHistory.map((turn, idx) => (
              <div key={idx} className={`message ${turn.role}`}>
                <strong>{turn.role === 'user' ? 'You' : selectedCharacter.name}:</strong>
                <p>{turn.content}</p>
              </div>
            ))}
          </div>
          
          {error && <p className="error">{error}</p>}
          
          <div className="input-area">
            <input
              type="text"
              placeholder="Type your message..."
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSendMessage(e.currentTarget.value);
                  e.currentTarget.value = '';
                }
              }}
              disabled={isLoading}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
```

---

## Error Handling

All endpoints return errors in this format:

```json
{
  "detail": "Error message description"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad request (invalid input)
- `404` - Not found (document/character not found)
- `500` - Internal server error

---

## Notes for Vite + React

1. **CORS is enabled** on the backend for development
2. Use `import.meta.env.VITE_API_URL` for environment variables
3. Install axios if you prefer it over fetch: `npm install axios`
4. Consider using React Query for better state management: `npm install @tanstack/react-query`

---

## Quick Start

1. Start backend: `python run.py`
2. Backend runs on: `http://localhost:8000`
3. API docs available at: `http://localhost:8000/docs`
4. Start frontend: `npm run dev`
5. Frontend typically runs on: `http://localhost:5173`

---

## Testing Endpoints

You can test all endpoints using the interactive API docs at:
```
http://localhost:8000/docs
```

This provides a Swagger UI where you can try all endpoints directly from the browser.
