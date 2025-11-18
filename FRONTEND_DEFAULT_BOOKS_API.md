# Default Books Feature - Frontend Integration Guide

## Overview
Add a "Featured Books" section on the homepage where users can instantly chat with characters from pre-loaded books without uploading PDFs.

---

## API Endpoints

**Base URL:** `http://localhost:8000/api/v1`

### 1. Get All Default Books

**Endpoint:** `GET /default-books`

**Response:**
```json
{
  "status": "success",
  "books": [
    {
      "book_id": "harry_potter_1",
      "document_id": "default_hp1_doc_001",
      "title": "Harry Potter and the Philosopher's Stone",
      "author": "J.K. Rowling",
      "cover_image": "/static/covers/harry_potter.jpg",
      "description": "The magical journey of a young wizard at Hogwarts School of Witchcraft and Wizardry.",
      "is_default": true,
      "genre": "Fantasy",
      "published_year": 1997
    },
    {
      "book_id": "chronicles_narnia",
      "document_id": "default_narnia_doc_002",
      "title": "The Chronicles of Narnia: The Lion, the Witch and the Wardrobe",
      "author": "C.S. Lewis",
      "cover_image": "/static/covers/chronicles_of_narnia.jpg",
      "description": "A magical land beyond the wardrobe where a great lion battles an evil witch.",
      "is_default": true,
      "genre": "Fantasy",
      "published_year": 1950
    },
    {
      "book_id": "the_hobbit",
      "document_id": "default_hobbit_doc_003",
      "title": "The Hobbit",
      "author": "J.R.R. Tolkien",
      "cover_image": "/static/covers/the_hobbit.jpg",
      "description": "An unexpected journey of a hobbit who discovers courage and friendship.",
      "is_default": true,
      "genre": "Fantasy",
      "published_year": 1937
    }
  ],
  "total": 3
}
```

---

### 2. Get Book Characters

**Endpoint:** `GET /default-books/{book_id}/characters`

**Example:** `GET /default-books/harry_potter_1/characters`

**Response:**
```json
{
  "status": "success",
  "document_id": "default_hp1_doc_001",
  "book_title": "Harry Potter and the Philosopher's Stone",
  "characters": [
    {
      "character_id": "char_harry_potter",
      "name": "Harry Potter",
      "aliases": ["Harry", "The Boy Who Lived", "Potter"],
      "description": "The Boy Who Lived, brave and loyal Gryffindor student characterized by his courage, determination, and willingness to sacrifice for others.",
      "role": "protagonist",
      "personality": {
        "personality_traits": ["brave", "loyal", "determined", "selfless", "curious"],
        "behavior_summary": "Courageous young wizard who values friendship and justice above all else.",
        "motivations": "To protect his friends, defeat evil, and discover his identity",
        "character_arc": "From orphaned boy to hero who embraces his destiny",
        "defining_moments": ["Confronting Voldemort", "Saving Hermione from the troll", "Choosing Gryffindor"]
      }
    },
    {
      "character_id": "char_hermione_granger",
      "name": "Hermione Granger",
      "aliases": ["Hermione", "Granger", "'Mione"],
      "description": "Brilliant and hardworking witch, known for her intelligence, loyalty, and fierce dedication to her studies and friends.",
      "role": "supporting",
      "personality": {
        "personality_traits": ["intelligent", "logical", "brave", "loyal", "perfectionist"],
        "behavior_summary": "Book-smart witch who uses logic and knowledge to solve problems.",
        "motivations": "To prove herself and help her friends succeed",
        "character_arc": "From rule-follower to brave rebel for what's right",
        "defining_moments": ["Solving the potions puzzle", "Time-Turner adventures", "Standing up to teachers"]
      }
    },
    {
      "character_id": "char_ron_weasley",
      "name": "Ron Weasley",
      "aliases": ["Ron", "Weasley", "Ronald"],
      "description": "Loyal and humorous friend from a large wizarding family, known for his bravery, chess skills, and unwavering friendship.",
      "role": "supporting",
      "personality": {
        "personality_traits": ["loyal", "humorous", "brave", "insecure", "caring"],
        "behavior_summary": "Comic relief who shows unexpected bravery when it matters most.",
        "motivations": "To step out of his brothers' shadows and prove his worth",
        "character_arc": "From overshadowed youngest brother to confident hero",
        "defining_moments": ["Sacrificing himself in chess game", "Facing his fears", "Loyal friendship"]
      }
    }
  ],
  "total_found": 3,
  "from_cache": true
}
```

---

### 3. Get Character Greeting

**Endpoint:** `POST /chat/greeting`

**Request Body:**
```json
{
  "document_id": "default_hp1_doc_001",
  "character_id": "char_harry_potter"
}
```

**Response:**
```json
{
  "status": "success",
  "character_name": "Harry Potter",
  "greeting": "Hello! I'm Harry Potter. The Boy Who Lived, brave and loyal Gryffindor student characterized by his courage, determination, and willingness to sacrifice for others. What brings you here?"
}
```

---

### 4. Chat with Character

**Endpoint:** `POST /chat`

**Request Body:**
```json
{
  "document_id": "default_hp1_doc_001",
  "character_id": "char_harry_potter",
  "message": "Tell me about your friends",
  "conversation_history": [
    {
      "role": "user",
      "content": "Hello!"
    },
    {
      "role": "assistant",
      "content": "Hello! I'm Harry Potter. What would you like to know?"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "character_name": "Harry Potter",
  "response": "Ron and Hermione are my best friends. Ron's been with me since the beginning, and Hermione's brilliance has saved us countless times. They're like family to me.",
  "context_chunks_used": 3,
  "relevant_context": [
    {
      "text": "Ron and Hermione were standing there...",
      "relevance_score": 0.89
    }
  ]
}
```

---

## React/TypeScript Implementation

### Types

```typescript
// types/defaultBooks.ts

export interface DefaultBook {
  book_id: string;
  document_id: string;
  title: string;
  author: string;
  cover_image: string;
  description: string;
  is_default: boolean;
  genre: string;
  published_year: number;
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
  };
}

export interface DefaultBooksResponse {
  status: string;
  books: DefaultBook[];
  total: number;
}

export interface CharactersResponse {
  status: string;
  document_id: string;
  book_title: string;
  characters: Character[];
  total_found: number;
  from_cache: boolean;
}
```

---

### API Service

```typescript
// services/defaultBooksApi.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const defaultBooksApi = {
  // Get all default books
  async getDefaultBooks(): Promise<DefaultBooksResponse> {
    const response = await fetch(`${API_BASE_URL}/default-books`);
    if (!response.ok) throw new Error('Failed to fetch default books');
    return response.json();
  },

  // Get book details
  async getBook(bookId: string): Promise<DefaultBook> {
    const response = await fetch(`${API_BASE_URL}/default-books/${bookId}`);
    if (!response.ok) throw new Error('Failed to fetch book');
    const data = await response.json();
    return data.book;
  },

  // Get book characters
  async getBookCharacters(bookId: string): Promise<CharactersResponse> {
    const response = await fetch(`${API_BASE_URL}/default-books/${bookId}/characters`);
    if (!response.ok) throw new Error('Failed to fetch characters');
    return response.json();
  },

  // Get character greeting (reuse existing chat API)
  async getCharacterGreeting(documentId: string, characterId: string) {
    const response = await fetch(`${API_BASE_URL}/chat/greeting`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: documentId, character_id: characterId })
    });
    if (!response.ok) throw new Error('Failed to get greeting');
    return response.json();
  },

  // Chat with character (reuse existing chat API)
  async chatWithCharacter(
    documentId: string,
    characterId: string,
    message: string,
    conversationHistory: Array<{ role: string; content: string }>
  ) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        document_id: documentId,
        character_id: characterId,
        message,
        conversation_history: conversationHistory
      })
    });
    if (!response.ok) throw new Error('Failed to send message');
    return response.json();
  }
};
```

---

### React Component Example

```tsx
// components/DefaultBooks.tsx

import { useState, useEffect } from 'react';
import { defaultBooksApi } from '../services/defaultBooksApi';
import type { DefaultBook, Character } from '../types/defaultBooks';

export const DefaultBooksSection = () => {
  const [books, setBooks] = useState<DefaultBook[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBooks();
  }, []);

  const loadBooks = async () => {
    try {
      const data = await defaultBooksApi.getDefaultBooks();
      setBooks(data.books);
    } catch (error) {
      console.error('Failed to load books:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading featured books...</div>;

  return (
    <section className="default-books">
      <h2>⭐ Featured Books</h2>
      <div className="books-grid">
        {books.map(book => (
          <BookCard key={book.book_id} book={book} />
        ))}
      </div>
    </section>
  );
};

const BookCard = ({ book }: { book: DefaultBook }) => {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [showCharacters, setShowCharacters] = useState(false);

  const loadCharacters = async () => {
    if (characters.length > 0) {
      setShowCharacters(!showCharacters);
      return;
    }

    try {
      const data = await defaultBooksApi.getBookCharacters(book.book_id);
      setCharacters(data.characters);
      setShowCharacters(true);
    } catch (error) {
      console.error('Failed to load characters:', error);
    }
  };

  return (
    <div className="book-card">
      <img src={book.cover_image} alt={book.title} />
      <h3>{book.title}</h3>
      <p className="author">{book.author}</p>
      <p className="description">{book.description}</p>
      <button onClick={loadCharacters}>
        {showCharacters ? 'Hide Characters' : 'View Characters'}
      </button>

      {showCharacters && (
        <div className="characters-list">
          {characters.map(character => (
            <CharacterCard
              key={character.character_id}
              character={character}
              documentId={book.document_id}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const CharacterCard = ({ 
  character, 
  documentId 
}: { 
  character: Character; 
  documentId: string;
}) => {
  const handleStartChat = () => {
    // Navigate to chat page with document_id and character_id
    window.location.href = `/chat?document=${documentId}&character=${character.character_id}`;
  };

  return (
    <div className="character-card">
      <h4>{character.name}</h4>
      <p>{character.description}</p>
      <span className="role">{character.role}</span>
      <button onClick={handleStartChat}>Chat Now</button>
    </div>
  );
};
```

---

## User Flow

1. **Homepage:** Display 3 featured books with covers
2. **Click Book:** Show list of characters from that book
3. **Click Character:** Navigate to chat page
4. **Chat Page:** 
   - Load greeting using `document_id` and `character_id`
   - Use existing chat interface
   - Chat works the same as uploaded books

---

## Key Points

✅ **No Upload Required** - Books and characters are pre-loaded
✅ **Instant Access** - Characters available immediately
✅ **Same Chat API** - Use existing `/chat` and `/chat/greeting` endpoints
✅ **Just Pass IDs** - Use `document_id` from default books
✅ **Static Covers** - Images served from `/static/covers/`

---

## Example: Full User Journey

```typescript
// 1. Load default books on homepage
const { books } = await defaultBooksApi.getDefaultBooks();

// 2. User clicks "Harry Potter" book
const { characters } = await defaultBooksApi.getBookCharacters('harry_potter_1');

// 3. User clicks "Harry Potter" character
const documentId = 'default_hp1_doc_001';
const characterId = 'char_harry_potter';

// 4. Get greeting
const { greeting } = await defaultBooksApi.getCharacterGreeting(documentId, characterId);
// Display: "Hello! I'm Harry Potter. The Boy Who Lived..."

// 5. User sends message
const response = await defaultBooksApi.chatWithCharacter(
  documentId,
  characterId,
  "Tell me about Hogwarts",
  []
);
// Display: Character's response
```

---

## Important Notes

⚠️ **RAG Context:** Default books are NOT indexed in ChromaDB yet. Characters will respond based on personality only, not specific book content.

✅ **To Enable Full RAG:**
1. Add PDF files for default books
2. Process and index them with matching `document_id` values
3. Then chat will include book-specific context

---

## Quick Test Commands

```bash
# Test API endpoints
curl http://localhost:8000/api/v1/default-books
curl http://localhost:8000/api/v1/default-books/harry_potter_1/characters
```
