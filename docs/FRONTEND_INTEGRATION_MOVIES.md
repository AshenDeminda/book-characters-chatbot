# Frontend Integration Guide - Default Movies Feature

## Overview
The backend now supports **pre-loaded movies** with characters, identical to the existing books feature. Users can chat with movie characters and their conversation history is automatically saved to the database.

## Available Movies
1. **The Shawshank Redemption** (1994)
   - Characters: Andy Dufresne, Red, Warden Norton
   
2. **The Godfather** (1972)
   - Characters: Vito Corleone, Michael Corleone, Sonny Corleone
   
3. **Inception** (2010)
   - Characters: Dom Cobb, Arthur, Ariadne

**Total: 3 movies with 9 pre-loaded characters**

---

## API Endpoints

Base URL: `http://localhost:8000/api/v1`

### 1. Get All Movies
```http
GET /default-movies
```

**Response:**
```json
{
  "movies": [
    {
      "movie_id": "the_shawshank_redemption",
      "document_id": "default_movie_shawshank_001",
      "title": "The Shawshank Redemption",
      "director": "Frank Darabont",
      "year": 1994,
      "genre": "Drama",
      "description": "Two imprisoned men bond over a number of years...",
      "cover_image": null
    }
  ]
}
```

### 2. Get Specific Movie Details
```http
GET /default-movies/{movie_id}
```

**Example:**
```http
GET /default-movies/the_shawshank_redemption
```

**Response:** Same structure as movie object above

### 3. Get All Characters from a Movie
```http
GET /default-movies/{movie_id}/characters
```

**Example:**
```http
GET /default-movies/the_shawshank_redemption/characters
```

**Response:**
```json
{
  "movie_id": "the_shawshank_redemption",
  "document_id": "default_movie_shawshank_001",
  "movie_title": "The Shawshank Redemption",
  "characters": [
    {
      "character_id": "char_andy_dufresne",
      "name": "Andy Dufresne",
      "actor": "Tim Robbins",
      "role": "Protagonist",
      "description": "A banker wrongfully convicted of murder...",
      "personality_traits": ["Intelligent", "Patient", "Determined"],
      "background": "Former vice president of a bank...",
      "motivations": "To prove his innocence and escape...",
      "relationships": "Close friend of Red...",
      "character_arc": "Transforms from a quiet newcomer..."
    }
  ]
}
```

### 4. Get Specific Character Details
```http
GET /default-movies/{movie_id}/characters/{character_id}
```

**Example:**
```http
GET /default-movies/the_shawshank_redemption/characters/char_andy_dufresne
```

**Response:** Same as individual character object above

---

## Chat Integration

**IMPORTANT:** Movie chat uses the **exact same endpoints** as books. The backend automatically detects whether the user is chatting with a movie or book character based on the `document_id`.

### Chat Endpoints (Shared with Books)

#### 1. Get Greeting Message
```http
POST /chat/greeting
Content-Type: application/json

{
  "document_id": "default_movie_shawshank_001",
  "character_id": "char_andy_dufresne"
}
```

**Response:**
```json
{
  "character_name": "Andy Dufresne",
  "greeting": "Hello, I'm Andy Dufresne. Hope is a good thing..."
}
```

#### 2. Send Chat Message
```http
POST /chat
Content-Type: application/json

{
  "document_id": "default_movie_shawshank_001",
  "character_id": "char_andy_dufresne",
  "user_message": "What was it like in Shawshank?"
}
```

**Response:**
```json
{
  "character_name": "Andy Dufresne",
  "response": "Shawshank was a place that tested every fiber...",
  "conversation_history": [
    {
      "role": "user",
      "content": "What was it like in Shawshank?"
    },
    {
      "role": "assistant",
      "content": "Shawshank was a place that tested..."
    }
  ]
}
```

#### 3. Stream Chat Response (SSE)
```http
POST /chat/stream
Content-Type: application/json

{
  "document_id": "default_movie_shawshank_001",
  "character_id": "char_andy_dufresne",
  "user_message": "Tell me about hope"
}
```

**Response:** Server-Sent Events stream

---

## Chat History Persistence

**Automatic Feature:** Chat history is automatically saved to the database for movie characters (same as books).

### Get Conversation History
```http
GET /chat-session/history?document_id=default_movie_shawshank_001&character_id=char_andy_dufresne
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "document_id": "default_movie_shawshank_001",
  "character_id": "char_andy_dufresne",
  "character_name": "Andy Dufresne",
  "conversation_history": [
    {
      "role": "user",
      "content": "What was it like in Shawshank?"
    },
    {
      "role": "assistant",
      "content": "Shawshank was a place..."
    }
  ]
}
```

### Clear Conversation History
```http
DELETE /chat-session/clear?document_id=default_movie_shawshank_001&character_id=char_andy_dufresne
```

---

## Frontend Implementation Guide

### Step 1: Create Movies Section UI
Add a new section/tab similar to your Books section:
- Display 3 movie cards with titles, directors, years, and genres
- Show "Chat with Characters" button for each movie

### Step 2: Fetch and Display Movies
```javascript
// Fetch all movies
async function fetchMovies() {
  const response = await fetch('http://localhost:8000/api/v1/default-movies');
  const data = await response.json();
  return data.movies; // Array of 3 movies
}

// Display movies in UI
const movies = await fetchMovies();
movies.forEach(movie => {
  // Render movie card with title, director, year, genre, description
});
```

### Step 3: Fetch and Display Characters
```javascript
// When user clicks on a movie
async function fetchCharacters(movieId) {
  const response = await fetch(
    `http://localhost:8000/api/v1/default-movies/${movieId}/characters`
  );
  const data = await response.json();
  return data.characters; // Array of 3 characters per movie
}

// Display characters
const characters = await fetchCharacters('the_shawshank_redemption');
characters.forEach(character => {
  // Render character card with name, actor, role, description
});
```

### Step 4: Initialize Chat
```javascript
// When user selects a character
async function startChat(documentId, characterId) {
  // 1. Load existing conversation history
  const historyResponse = await fetch(
    `http://localhost:8000/api/v1/chat-session/history?document_id=${documentId}&character_id=${characterId}`
  );
  const historyData = await historyResponse.json();
  
  // Display existing messages if any
  if (historyData.conversation_history.length > 0) {
    displayMessages(historyData.conversation_history);
  }
  
  // 2. Get greeting if no history
  if (historyData.conversation_history.length === 0) {
    const greetingResponse = await fetch(
      'http://localhost:8000/api/v1/chat/greeting',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: documentId, character_id: characterId })
      }
    );
    const greetingData = await greetingResponse.json();
    displayMessage('assistant', greetingData.greeting);
  }
}
```

### Step 5: Send Messages
```javascript
// **SAME CODE AS BOOKS** - No changes needed!
async function sendMessage(documentId, characterId, userMessage) {
  const response = await fetch('http://localhost:8000/api/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id: documentId,
      character_id: characterId,
      user_message: userMessage
    })
  });
  
  const data = await response.json();
  
  // Display user message
  displayMessage('user', userMessage);
  
  // Display character response
  displayMessage('assistant', data.response);
  
  // History is automatically saved by backend!
}
```

### Step 6: Streaming (Optional)
```javascript
// **SAME CODE AS BOOKS** - No changes needed!
async function sendMessageStream(documentId, characterId, userMessage) {
  const response = await fetch('http://localhost:8000/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_id: documentId,
      character_id: characterId,
      user_message: userMessage
    })
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  let fullResponse = '';
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') break;
        
        fullResponse += data;
        updateMessage('assistant', fullResponse); // Update UI incrementally
      }
    }
  }
}
```

---

## Document ID Format

**Critical for proper detection:**
- **Books:** `default_hp1_doc_001`, `default_narnia1_doc_001`, etc.
- **Movies:** `default_movie_shawshank_001`, `default_movie_godfather_002`, etc.

The backend detects movies by checking if `"movie"` is in the `document_id` string.

---

## Character ID Format

All movie characters use the format: `char_{character_name}`

Examples:
- `char_andy_dufresne`
- `char_red`
- `char_vito_corleone`
- `char_dom_cobb`

---

## Cover Images (Optional)

Cover images are **not** served by the backend. You should add them to your frontend assets:

1. Download/add these images to your frontend:
   - `shawshank.jpg` - The Shawshank Redemption poster
   - `godfather.jpg` - The Godfather poster
   - `inception.jpg` - Inception poster

2. Map `movie_id` to image paths:
```javascript
const movieCovers = {
  'the_shawshank_redemption': '/assets/movies/shawshank.jpg',
  'the_godfather': '/assets/movies/godfather.jpg',
  'inception': '/assets/movies/inception.jpg'
};
```

---

## Complete Movie and Character IDs Reference

### The Shawshank Redemption
- **movie_id:** `the_shawshank_redemption`
- **document_id:** `default_movie_shawshank_001`
- **Characters:**
  - Andy Dufresne: `char_andy_dufresne`
  - Red: `char_red`
  - Warden Norton: `char_warden_norton`

### The Godfather
- **movie_id:** `the_godfather`
- **document_id:** `default_movie_godfather_002`
- **Characters:**
  - Vito Corleone: `char_vito_corleone`
  - Michael Corleone: `char_michael_corleone`
  - Sonny Corleone: `char_sonny_corleone`

### Inception
- **movie_id:** `inception`
- **document_id:** `default_movie_inception_003`
- **Characters:**
  - Dom Cobb: `char_dom_cobb`
  - Arthur: `char_arthur`
  - Ariadne: `char_ariadne`

---

## Testing Checklist

- [ ] Fetch and display all 3 movies
- [ ] Click on each movie and see 3 characters
- [ ] Select character and see greeting message
- [ ] Send messages and receive responses
- [ ] Switch to different character and back - verify chat history persists
- [ ] Test streaming endpoint (if using SSE)
- [ ] Clear conversation history functionality
- [ ] Verify chat works across page refreshes

---

## Key Differences from Books

1. **Movie metadata includes:** `director`, `year`, `genre` (books don't have these)
2. **Character data includes:** `actor` field (books don't have this)
3. **Document IDs:** Movies have `"movie"` in the ID for automatic detection
4. **Everything else is identical:** Same chat API, same history persistence, same response format

---

## Error Handling

Handle these potential errors:

```javascript
// Movie not found
if (response.status === 404) {
  console.error('Movie or character not found');
}

// Character loading failed
if (data.error) {
  console.error('Failed to load character:', data.error);
}

// Chat service errors
if (response.status === 500) {
  console.error('Chat service error - check backend logs');
}
```

---

## Need Help?

- **Swagger Docs:** http://localhost:8000/docs (see "Default Movies" section)
- **Test endpoints:** Use Postman or curl to verify API responses
- **Backend logs:** Check terminal for detailed error messages

---

## Summary for Quick Implementation

**You can literally copy-paste your Books component code and change:**
1. API endpoint: `/default-books` → `/default-movies`
2. Display fields: Add `director`, `year`, `genre`, `actor`
3. **Chat code:** NO CHANGES NEEDED - exact same endpoints!

The backend handles everything automatically based on the `document_id` format. Just pass `default_movie_*` IDs instead of `default_hp1_doc_*` IDs.
