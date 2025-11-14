"""
Test script for character entity resolution (alias merging)
Usage: python test_entity_resolution.py <document_id>

This script tests the entity resolution feature that merges character aliases
like "Shin/Undertaker/Reaper" into a single character with all name variants.
"""
import sys
import requests
import json

def test_entity_resolution(document_id: str):
    """Test character extraction with entity resolution"""
    url = "http://localhost:8000/api/v1/characters/extract-characters"
    
    payload = {
        "document_id": document_id,
        "max_characters": 10,
        "include_personality": False  # Fast test without personality
    }
    
    print("="*80)
    print("🔍 TESTING ENTITY RESOLUTION")
    print("="*80)
    print(f"\nDocument ID: {document_id}")
    print("Extracting characters with alias merging...\n")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✅ Status: {result['status']}")
        print(f"📊 Total unique characters: {result['total_found']}\n")
        print("="*80)
        
        for i, char in enumerate(result['characters'], 1):
            print(f"\n{i}. CHARACTER: {char['name']}")
            print(f"   ID: {char['character_id']}")
            print(f"   Role: {char['role']}")
            
            # Show aliases
            aliases = char.get('aliases', [])
            if len(aliases) > 1:
                print(f"   ✨ Aliases ({len(aliases)}): {', '.join(aliases)}")
            else:
                print(f"   Aliases: None detected")
            
            print(f"   Description: {char['description'][:100]}...")
            print()
        
        print("="*80)
        
        # Check for successful merging
        all_names = []
        for char in result['characters']:
            all_names.extend(char.get('aliases', [char['name']]))
        
        print(f"\n📝 Summary:")
        print(f"   Total unique characters: {len(result['characters'])}")
        print(f"   Total name variants found: {len(all_names)}")
        print(f"   Names merged: {len(all_names) - len(result['characters'])}")
        
        # Save to file
        output_file = f"entity_resolution_{document_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Full results saved to: {output_file}")
        
        # Show examples of merged characters
        merged_chars = [c for c in result['characters'] if len(c.get('aliases', [])) > 1]
        if merged_chars:
            print(f"\n🎯 Successfully merged {len(merged_chars)} characters with multiple aliases:")
            for char in merged_chars:
                print(f"   • {char['name']}: {' | '.join(char['aliases'])}")
        else:
            print("\n⚠️  No character aliases were merged. This might mean:")
            print("   - Characters only have one name in the text")
            print("   - Entity resolution needs tuning")
            print("   - AI didn't detect multiple name variants")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_entity_resolution.py <document_id>")
        print("\nExample:")
        print("  python test_entity_resolution.py fa0d116d-38ca-4de5-9f2b-611ddcde9d2f")
        print("\nThis will test if characters with multiple names (like 'Shin/Undertaker/Reaper')")
        print("are correctly merged into a single character with aliases.")
        sys.exit(1)
    
    document_id = sys.argv[1]
    test_entity_resolution(document_id)
