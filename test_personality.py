"""
Test script for character personality extraction
Usage: python test_personality.py <document_id>
"""
import sys
import requests
import json

def extract_characters_with_personality(document_id: str):
    """Extract characters with personality summaries"""
    url = "http://localhost:8000/api/v1/characters/extract-characters"
    
    payload = {
        "document_id": document_id,
        "max_characters": 5,
        "include_personality": True  # Request personality analysis
    }
    
    print(f"Extracting characters with personality from document: {document_id}")
    print("This may take a minute as AI analyzes each character...\n")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"Status: {result['status']}")
        print(f"Total characters found: {result['total_found']}\n")
        print("="*80)
        
        for char in result['characters']:
            print(f"\n📖 CHARACTER: {char['name']}")
            print(f"   Role: {char['role']}")
            print(f"   ID: {char['character_id']}")
            print(f"\n   Description: {char['description']}")
            
            if char.get('personality'):
                personality = char['personality']
                print(f"\n   🎭 PERSONALITY ANALYSIS:")
                print(f"   Traits: {', '.join(personality.get('personality_traits', []))}")
                print(f"\n   Behavior: {personality.get('behavior_summary', 'N/A')}")
                print(f"\n   Motivations: {personality.get('motivations', 'N/A')}")
                print(f"\n   Character Arc: {personality.get('character_arc', 'N/A')}")
                
                defining_moments = personality.get('defining_moments', [])
                if defining_moments:
                    print(f"\n   Defining Moments:")
                    for i, moment in enumerate(defining_moments, 1):
                        print(f"   {i}. {moment}")
            else:
                print(f"\n   ⚠️  Personality analysis not available")
            
            print("\n" + "="*80)
        
        # Save to file
        output_file = f"characters_with_personality_{document_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Full results saved to: {output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_personality.py <document_id>")
        print("\nExample:")
        print("  python test_personality.py fa0d116d-38ca-4de5-9f2b-611ddcde9d2f")
        sys.exit(1)
    
    document_id = sys.argv[1]
    extract_characters_with_personality(document_id)
