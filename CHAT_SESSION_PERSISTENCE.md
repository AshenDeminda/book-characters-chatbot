# Chat Session Persistence - Frontend Integration

## Overview
Backend now stores conversation history for default books. When users switch between characters, their chat history is preserved and automatically loaded.

## How It Works

**Backend automatically:**
1. ✅ Saves every message exchange to database
2. ✅ Loads history when user returns to a character
3. ✅ Stores separately for each character (Harry Potter chat won't mix with Hermione chat)

**Frontend needs to:**
1. Load history when user selects a character
2. Optionally: Show "Clear Chat" button
3. Optionally: Show list of active chats

---

## New API Endpoints

### 1. Load Chat History (GET)

**Endpoint:** `GET /api/v1/chat/session/history?document_id={doc_id}&character_id={char_id}`

**When to call:** When user clicks on a character to start chatting

**Example:**
```javascript
const response = await fetch(
  `http://localhost:8000/api/v1/chat/session/history?document_id=default_hp1_doc_001&character_id=char_harry_potter`
);
const data = await response.json();

// data.conversation_history = [
//   { role: "user", content: "Hello!" },
//   { role: "assistant", content: "Hi there!" },
//   ...
// ]
```

**Response:**
```json
{
  "status": "success",
  "document_id": "default_hp1_doc_001",
  "character_id": "char_harry_potter",
  "conversation_history": [
    {
      "role": "user",
      "content": "Tell me about Hogwarts"
    },
    {
      "role": "assistant",
      "content": "Hogwarts is a magical school..."
    }
  ],
  "total_messages": 6
}
```

---

### 2. Save Message (POST) - **AUTOMATIC, No Frontend Action Needed**

**Endpoint:** `POST /api/v1/chat/session/save`

**Backend automatically saves after each chat response**

The `/chat` and `/chat/stream` endpoints now automatically call this internally, so frontend doesn't need to do anything special.

---

### 3. Clear Chat History (DELETE)

**Endpoint:** `DELETE /api/v1/chat/session/clear?document_id={doc_id}&character_id={char_id}`

**When to call:** When user clicks "Clear Chat" or "New Conversation" button

**Example:**
```javascript
const response = await fetch(
  `http://localhost:8000/api/v1/chat/session/clear?document_id=default_hp1_doc_001&character_id=char_harry_potter`,
  { method: 'DELETE' }
);
```

**Response:**
```json
{
  "status": "success",
  "message": "Chat session cleared successfully"
}
```

---

### 4. List All Chats for a Book (Optional)

**Endpoint:** `GET /api/v1/chat/session/list?document_id={doc_id}`

**When to call:** To show "Continue conversations" or "Recent chats" section

**Example:**
```javascript
const response = await fetch(
  `http://localhost:8000/api/v1/chat/session/list?document_id=default_hp1_doc_001`
);
```

**Response:**
```json
{
  "status": "success",
  "document_id": "default_hp1_doc_001",
  "sessions": [
    {
      "session_id": "default_hp1_doc_001_char_harry_potter",
      "character_id": "char_harry_potter",
      "character_name": "Harry Potter",
      "message_count": 12,
      "created_at": "2025-11-18T10:30:00",
      "updated_at": "2025-11-18T11:45:00"
    },
    {
      "session_id": "default_hp1_doc_001_char_hermione_granger",
      "character_id": "char_hermione_granger",
      "character_name": "Hermione Granger",
      "message_count": 8,
      "created_at": "2025-11-18T09:15:00",
      "updated_at": "2025-11-18T10:00:00"
    }
  ],
  "total_sessions": 2
}
```

---

## Frontend Implementation Example

### React/TypeScript Example

```typescript
// When user selects a character
const loadCharacterChat = async (documentId: string, characterId: string) => {
  try {
    // 1. Load history
    const historyResponse = await fetch(
      `${API_URL}/chat/session/history?document_id=${documentId}&character_id=${characterId}`
    );
    const historyData = await historyResponse.json();
    
    // 2. Set conversation state
    setConversationHistory(historyData.conversation_history || []);
    
    // 3. Get greeting if no history
    if (historyData.conversation_history.length === 0) {
      const greetingResponse = await fetch(`${API_URL}/chat/greeting`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: documentId, character_id: characterId })
      });
      const greeting = await greetingResponse.json();
      
      setConversationHistory([
        { role: 'assistant', content: greeting.greeting }
      ]);
    }
  } catch (error) {
    console.error('Error loading chat:', error);
  }
};

// Clear chat button
const clearChat = async () => {
  try {
    await fetch(
      `${API_URL}/chat/session/clear?document_id=${documentId}&character_id=${characterId}`,
      { method: 'DELETE' }
    );
    
    setConversationHistory([]);
    // Show success message
  } catch (error) {
    console.error('Error clearing chat:', error);
  }
};
```

---

## User Flow

### First Time Chatting with a Character:
1. User selects Harry Potter
2. Frontend calls `GET /chat/session/history` → Returns empty array
3. Frontend calls `POST /chat/greeting` → Shows greeting
4. User chats → Backend auto-saves messages

### Returning to a Character:
1. User selects Harry Potter again (maybe switched to Hermione and back)
2. Frontend calls `GET /chat/session/history` → Returns previous messages
3. Frontend displays all previous messages
4. User continues chatting → Backend continues saving

### Clearing History:
1. User clicks "Clear Chat" button
2. Frontend calls `DELETE /chat/session/clear`
3. Frontend clears UI messages
4. Next chat starts fresh

---

## Important Notes

✅ **Only for default books** - Uploaded books will get this feature later
✅ **Automatic saving** - Backend saves after every response, no frontend action needed
✅ **Per-character storage** - Each character has separate conversation history
✅ **Database persistent** - History survives server restarts

---

## Optional UI Enhancements

### Show "Continue Conversations"
```typescript
// On book page, show which characters user has chatted with
const { sessions } = await fetch(
  `${API_URL}/chat/session/list?document_id=${bookId}`
).then(r => r.json());

// Display: "Continue conversation with Harry (12 messages)"
```

### Add "New Chat" Button
```typescript
<button onClick={clearChat}>
  🗑️ Clear Chat & Start Fresh
</button>
```

### Show Message Count
```typescript
const history = await loadHistory();
<div>Previous messages: {history.total_messages}</div>
```

---

## Testing

### Test Scenario 1: Persistence
1. Chat with Harry Potter
2. Switch to Hermione
3. Switch back to Harry → Should see previous messages ✅

### Test Scenario 2: Clear
1. Chat with Harry Potter
2. Click "Clear Chat"
3. Should start fresh conversation ✅

### Test Scenario 3: Multiple Characters
1. Chat with Harry
2. Chat with Hermione
3. Chat with Ron
4. Switch between them → Each should have own history ✅
