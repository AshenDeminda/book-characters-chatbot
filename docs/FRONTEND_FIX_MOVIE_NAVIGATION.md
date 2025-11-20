# Frontend Fix: Movie Character Navigation Issue

## Problem
When selecting a movie character, the frontend is navigating to the "extract character" page. This is **WRONG** for default movies because:
- Extract character page is for **uploaded books only** (AI extraction required)
- Default movies have **pre-loaded characters** (no extraction needed)
- Should go directly to chat page

## Root Cause
Frontend is treating default movies the same as uploaded books. The flow should be different:

### Current (WRONG) Flow for Movies:
```
Select Movie → Extract Characters Page → Chat Page
                     ❌ WRONG!
```

### Correct Flow for Movies:
```
Select Movie → View Characters → Select Character → Chat Page (DIRECT)
                                                    ✅ CORRECT!
```

---

## Solution

### Step 1: Identify Content Type in Frontend

Add detection logic to differentiate between uploaded books and default content:

```javascript
function isDefaultContent(documentId) {
  // Default books start with "default_hp1_", "default_narnia1_", etc.
  // Default movies start with "default_movie_"
  return documentId.startsWith('default_');
}

function isDefaultMovie(documentId) {
  return documentId.includes('movie');
}

function isDefaultBook(documentId) {
  return documentId.startsWith('default_') && !documentId.includes('movie');
}
```

### Step 2: Conditional Navigation Logic

Update your navigation/routing code:

```javascript
function handleCharacterSelection(documentId, characterId, characterName) {
  if (isDefaultContent(documentId)) {
    // Default content (books OR movies) - characters are pre-loaded
    // Skip extraction, go directly to chat
    navigateToChat(documentId, characterId, characterName);
  } else {
    // Uploaded book - needs extraction first
    navigateToExtractCharacters(documentId);
  }
}

function navigateToChat(documentId, characterId, characterName) {
  // Navigate directly to chat page
  // Example: /chat?document=${documentId}&character=${characterId}
  router.push({
    path: '/chat',
    query: {
      documentId: documentId,
      characterId: characterId,
      characterName: characterName
    }
  });
}

function navigateToExtractCharacters(documentId) {
  // Only for uploaded books
  router.push({
    path: '/extract-characters',
    query: {
      documentId: documentId
    }
  });
}
```

### Step 3: Movie Selection Flow

When user clicks on a movie card:

```javascript
async function handleMovieClick(movieId) {
  // 1. Fetch characters for this movie
  const response = await fetch(
    `http://localhost:8000/api/v1/default-movies/${movieId}/characters`
  );
  const data = await response.json();
  
  // 2. Show characters selection UI
  displayCharacters(data.characters, data.document_id);
}

function displayCharacters(characters, documentId) {
  // Show a modal or page with character cards
  characters.forEach(character => {
    // Each character card should have a "Chat Now" button
    renderCharacterCard(character, documentId);
  });
}

function renderCharacterCard(character, documentId) {
  // When user clicks "Chat Now" or character card
  onCharacterClick(() => {
    // Go DIRECTLY to chat (no extraction page)
    navigateToChat(
      documentId,
      character.character_id,
      character.name
    );
  });
}
```

---

## Complete Example: React Component

```jsx
import { useNavigate } from 'react-router-dom';

function MovieCharacterSelection({ movie }) {
  const navigate = useNavigate();
  const [characters, setCharacters] = useState([]);

  useEffect(() => {
    fetchCharacters();
  }, [movie]);

  const fetchCharacters = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/default-movies/${movie.movie_id}/characters`
      );
      const data = await response.json();
      setCharacters(data.characters);
    } catch (error) {
      console.error('Failed to fetch characters:', error);
    }
  };

  const handleCharacterClick = (character) => {
    // DIRECT navigation to chat - NO extraction page
    navigate('/chat', {
      state: {
        documentId: movie.document_id,
        characterId: character.character_id,
        characterName: character.name,
        isPreloaded: true  // Flag to indicate pre-loaded character
      }
    });
  };

  return (
    <div className="character-selection">
      <h2>Select a character from {movie.title}</h2>
      <div className="characters-grid">
        {characters.map((character) => (
          <div 
            key={character.character_id}
            className="character-card"
            onClick={() => handleCharacterClick(character)}
          >
            <h3>{character.name}</h3>
            <p className="actor">Played by: {character.actor}</p>
            <p className="role">{character.role}</p>
            <p className="description">{character.description}</p>
            <button className="chat-button">Chat Now</button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Vue.js Example

```vue
<template>
  <div class="movie-characters">
    <h2>Select a character from {{ movie.title }}</h2>
    <div class="characters-grid">
      <div 
        v-for="character in characters" 
        :key="character.character_id"
        class="character-card"
        @click="startChat(character)"
      >
        <h3>{{ character.name }}</h3>
        <p class="actor">{{ character.actor }}</p>
        <p class="role">{{ character.role }}</p>
        <p class="description">{{ character.description }}</p>
        <button class="btn-primary">Chat Now</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['movie'],
  data() {
    return {
      characters: []
    };
  },
  async mounted() {
    await this.fetchCharacters();
  },
  methods: {
    async fetchCharacters() {
      try {
        const response = await fetch(
          `http://localhost:8000/api/v1/default-movies/${this.movie.movie_id}/characters`
        );
        const data = await response.json();
        this.characters = data.characters;
      } catch (error) {
        console.error('Failed to fetch characters:', error);
      }
    },
    startChat(character) {
      // Navigate DIRECTLY to chat - skip extraction
      this.$router.push({
        name: 'Chat',
        query: {
          documentId: this.movie.document_id,
          characterId: character.character_id,
          characterName: character.name
        }
      });
    }
  }
};
</script>
```

---

## Router Configuration Example

Update your router to handle direct navigation:

```javascript
const routes = [
  {
    path: '/movies',
    name: 'Movies',
    component: MoviesPage
  },
  {
    path: '/movies/:movieId/characters',
    name: 'MovieCharacters',
    component: MovieCharactersPage
  },
  {
    path: '/chat',
    name: 'Chat',
    component: ChatPage,
    // No beforeEnter guard needed for default content
  },
  {
    path: '/books/extract-characters/:documentId',
    name: 'ExtractCharacters',
    component: ExtractCharactersPage,
    // Only for uploaded books
    beforeEnter: (to, from, next) => {
      const documentId = to.params.documentId;
      if (documentId.startsWith('default_')) {
        // Redirect default content away from extraction page
        next({ name: 'Chat', query: { documentId } });
      } else {
        next();
      }
    }
  }
];
```

---

## Backend Endpoints Summary (Already Working)

These endpoints are **ready** and don't need changes:

### For Movies:
1. `GET /api/v1/default-movies` - List movies ✅
2. `GET /api/v1/default-movies/{movie_id}/characters` - Get characters ✅
3. `POST /api/v1/chat/greeting` - Start chat ✅
4. `POST /api/v1/chat` - Send message ✅

### For Books:
1. `GET /api/v1/default-books` - List books ✅
2. `GET /api/v1/default-books/{book_id}/characters` - Get characters ✅
3. `POST /api/v1/chat/greeting` - Start chat ✅
4. `POST /api/v1/chat` - Send message ✅

**The backend is correct - only frontend routing needs fixing!**

---

## Key Differences: Uploaded Books vs Default Content

| Feature | Uploaded Books | Default Books/Movies |
|---------|---------------|---------------------|
| Character Extraction | ✅ Required (AI extraction) | ❌ Not needed (pre-loaded) |
| Extraction Page | ✅ Navigate here first | ❌ Skip this page |
| Character API | `POST /characters/extract-characters` | `GET /default-movies/{id}/characters` |
| Chat | After extraction complete | Immediate |

---

## Testing Checklist

After implementing the fix:

- [ ] Click on a movie → Should see characters list
- [ ] Click on a character → Should go **directly to chat** (not extraction page)
- [ ] Chat should work immediately with greeting message
- [ ] Same for default books (should skip extraction)
- [ ] Uploaded books should still go to extraction page
- [ ] Navigation history should be correct

---

## Quick Fix Summary

**Problem:** Movies navigate to extraction page  
**Cause:** Frontend treats all content the same way  
**Solution:** Add conditional navigation based on `document_id` format

**Change this:**
```javascript
// WRONG - Always go to extraction
handleSelect(documentId, characterId) {
  router.push('/extract-characters');
}
```

**To this:**
```javascript
// CORRECT - Skip extraction for default content
handleSelect(documentId, characterId) {
  if (documentId.startsWith('default_')) {
    router.push('/chat'); // Direct to chat
  } else {
    router.push('/extract-characters'); // Only for uploads
  }
}
```

---

## Need Help?

If you're still having issues, check:
1. Is `documentId` being passed correctly? (Should contain "default_movie_")
2. Is your router configured to allow direct chat navigation?
3. Are you using the correct character API endpoints?
4. Check browser console for any JavaScript errors

**The backend is working correctly. This is purely a frontend routing/navigation issue.**
