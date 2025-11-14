# Character Personality Analysis API

## Overview
The character extraction API now supports generating detailed personality and behavior summaries for each character using AI analysis.

## Endpoint
**POST** `/api/v1/characters/extract-characters`

## Request Body

```json
{
  "document_id": "string",
  "max_characters": 10,  // optional, default: 10
  "include_personality": false  // optional, default: false
}
```

### Parameters

- `document_id` (required): The UUID of the uploaded document
- `max_characters` (optional): Maximum number of characters to extract (default: 10)
- `include_personality` (optional): Whether to generate personality summaries (default: false)

## Response Format

### Without Personality (include_personality: false)

```json
{
  "status": "success",
  "document_id": "fa0d116d-38ca-4de5-9f2b-611ddcde9d2f",
  "total_found": 3,
  "characters": [
    {
      "character_id": "char_001",
      "name": "Pinocchio",
      "description": "A wooden puppet who wants to become a real boy",
      "role": "protagonist",
      "personality": null
    }
  ]
}
```

### With Personality (include_personality: true)

```json
{
  "status": "success",
  "document_id": "fa0d116d-38ca-4de5-9f2b-611ddcde9d2f",
  "total_found": 3,
  "characters": [
    {
      "character_id": "char_001",
      "name": "Pinocchio",
      "description": "A wooden puppet who wants to become a real boy",
      "role": "protagonist",
      "personality": {
        "personality_traits": [
          "Curious",
          "Naive",
          "Impulsive",
          "Good-hearted"
        ],
        "behavior_summary": "Pinocchio is an innocent and curious puppet who often acts impulsively without thinking of consequences. He is easily influenced by others but has a fundamentally good heart.",
        "motivations": "Desires to become a real boy and make his father Geppetto proud",
        "character_arc": "Learns through mistakes and adventures about honesty, responsibility, and what it means to be truly human",
        "defining_moments": [
          "His nose grows when he lies",
          "Disobeys the Blue Fairy and goes to Pleasure Island",
          "Saves Geppetto from the whale"
        ]
      }
    }
  ]
}
```

## Personality Object Structure

When `include_personality: true`, each character includes:

- **personality_traits**: Array of key personality traits (e.g., "brave", "curious", "kind")
- **behavior_summary**: 2-3 sentence summary of how the character behaves and interacts
- **motivations**: What drives this character
- **character_arc**: How they change or develop in the story
- **defining_moments**: Notable quotes or actions that define the character

## Performance Notes

- **Without personality**: Fast extraction (~5-10 seconds for 3 characters)
- **With personality**: Takes longer as AI analyzes each character individually (~30-60 seconds for 3 characters)

## Usage Examples

### Basic Character Extraction
```bash
curl -X POST http://localhost:8000/api/v1/characters/extract-characters \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "fa0d116d-38ca-4de5-9f2b-611ddcde9d2f"
  }'
```

### Character Extraction with Personality
```bash
curl -X POST http://localhost:8000/api/v1/characters/extract-characters \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "fa0d116d-38ca-4de5-9f2b-611ddcde9d2f",
    "include_personality": true
  }'
```

### Using Test Scripts

**Quick extraction (names only):**
```bash
python test_characters.py fa0d116d-38ca-4de5-9f2b-611ddcde9d2f
```

**Full personality analysis:**
```bash
python test_personality.py fa0d116d-38ca-4de5-9f2b-611ddcde9d2f
```

## Error Handling

- If personality generation fails for a character, the API continues processing other characters
- Failed personalities will have `personality: null` in the response
- The overall request will still succeed

## Implementation Details

1. Text is read from the chunks file
2. AI identifies main characters (using first 8000 chars)
3. If `include_personality: true`, for each character:
   - AI analyzes personality using first 10000 chars
   - Generates detailed psychological profile
   - Adds to character object
4. Returns complete character list with optional personality data
