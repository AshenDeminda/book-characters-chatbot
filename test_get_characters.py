"""
Quick script to get character IDs from an uploaded document
Usage: python test_get_characters.py <document_id>
"""
import sys
import requests

def get_characters(document_id: str):
    """Get all characters from a document"""
    url = f"http://localhost:8000/api/v1/characters/extract-characters/{document_id}"
    
    print("="*80)
    print("📋 GETTING CHARACTERS")
    print("="*80)
    print(f"\nDocument ID: {document_id}\n")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        characters = result.get('characters', [])
        
        if not characters:
            print("❌ No characters found in this document")
            return
        
        print(f"✅ Found {len(characters)} characters:\n")
        
        for char in characters:
            print(f"Character ID: {char['character_id']}")
            print(f"Name: {char['name']}")
            if char.get('aliases'):
                print(f"Aliases: {', '.join(char['aliases'])}")
            if char.get('personality'):
                print(f"Personality: {char['personality'][:100]}...")
            print("-" * 80)
        
        print(f"\n💡 To chat with a character, use:")
        print(f"   python test_chat.py {document_id} <character_id>")
        print(f"\nExample:")
        print(f"   python test_chat.py {document_id} {characters[0]['character_id']}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_get_characters.py <document_id>")
        print("\nExample:")
        print("  python test_get_characters.py fa0d116d-38ca-4de5-9f2b-611ddcde9d2f")
        sys.exit(1)
    
    document_id = sys.argv[1]
    get_characters(document_id)
