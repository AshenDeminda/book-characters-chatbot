"""
Production-Grade Character Extraction Test
Tests the improved extraction with:
1. Non-character filtering (insults, titles, groups)
2. Smart alias merging (full names over titles)
3. Pattern-based entity resolution

Usage: python test_production_extraction.py <document_id>
"""
import sys
import requests
import json

def test_production_extraction(document_id: str):
    """Test production-grade character extraction"""
    url = "http://localhost:8000/api/v1/characters/extract-characters"
    
    payload = {
        "document_id": document_id,
        "max_characters": 15,
        "include_personality": False
    }
    
    print("="*80)
    print("🎯 PRODUCTION-GRADE CHARACTER EXTRACTION TEST")
    print("="*80)
    print("\nFeatures being tested:")
    print("  ✓ Filters out insults (idiot, fool, princess)")
    print("  ✓ Filters out titles (lieutenant, captain, handler)")
    print("  ✓ Filters out groups (Eighty-Six, soldiers)")
    print("  ✓ Smart primary name selection (full names > callsigns)")
    print("  ✓ Pattern-based alias merging")
    print("\n" + "="*80)
    print(f"\nDocument ID: {document_id}\n")
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        print(f"✅ Status: {result['status']}")
        print(f"📊 Total unique characters: {result['total_found']}\n")
        print("="*80)
        
        # Categorize characters
        with_aliases = []
        without_aliases = []
        
        for char in result['characters']:
            if len(char.get('aliases', [])) > 1:
                with_aliases.append(char)
            else:
                without_aliases.append(char)
        
        # Show characters with merged aliases
        if with_aliases:
            print(f"\n✨ CHARACTERS WITH MERGED ALIASES ({len(with_aliases)}):\n")
            for i, char in enumerate(with_aliases, 1):
                print(f"{i}. {char['name']}")
                print(f"   ID: {char['character_id']}")
                print(f"   Role: {char['role']}")
                print(f"   Aliases ({len(char['aliases'])}): {' | '.join(char['aliases'])}")
                print(f"   Description: {char['description'][:80]}...")
                print()
        
        # Show characters without aliases
        if without_aliases:
            print(f"👤 UNIQUE CHARACTERS (no aliases detected) ({len(without_aliases)}):\n")
            for i, char in enumerate(without_aliases, 1):
                print(f"{i}. {char['name']}")
                print(f"   ID: {char['character_id']}")
                print(f"   Role: {char['role']}")
                print(f"   Description: {char['description'][:80]}...")
                print()
        
        print("="*80)
        
        # Statistics
        total_aliases = sum(len(char.get('aliases', [])) for char in result['characters'])
        merged_count = total_aliases - len(result['characters'])
        
        print(f"\n📈 EXTRACTION STATISTICS:")
        print(f"   Total unique characters: {len(result['characters'])}")
        print(f"   Characters with aliases: {len(with_aliases)}")
        print(f"   Total name variants: {total_aliases}")
        print(f"   Names merged: {merged_count}")
        
        # Quality checks
        print(f"\n🔍 QUALITY CHECKS:")
        
        # Check for filtered terms
        all_names = []
        for char in result['characters']:
            all_names.extend(char.get('aliases', [char['name']]))
        
        non_character_terms = {
            "idiot", "fool", "princess", "your majesty",
            "bloodstained queen", "bloody reina",
            "lieutenant", "captain", "commander",
            "eighty-six", "soldiers", "troops"
        }
        
        found_bad_terms = [name for name in all_names if name.lower() in non_character_terms]
        
        if found_bad_terms:
            print(f"   ⚠️  Found filtered terms that got through: {found_bad_terms}")
        else:
            print(f"   ✅ No insults/titles/groups detected")
        
        # Check primary name quality
        full_names = [c for c in result['characters'] if " " in c['name']]
        print(f"   {'✅' if len(full_names) > 0 else '⚠️ '} Full names used as primary: {len(full_names)}/{len(result['characters'])}")
        
        # Check for proper role distribution
        roles = {}
        for char in result['characters']:
            role = char.get('role', 'unknown')
            roles[role] = roles.get(role, 0) + 1
        
        print(f"   📊 Role distribution: {dict(roles)}")
        
        # Save results
        output_file = f"production_extraction_{document_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Full results saved to: {output_file}")
        
        # Recommendations
        print(f"\n💡 ANALYSIS:")
        if merged_count > 0:
            print(f"   ✅ Successfully merged {merged_count} character aliases")
        else:
            print(f"   ℹ️  No aliases merged (characters may have unique names only)")
        
        if len(result['characters']) < 3:
            print(f"   ⚠️  Very few characters extracted. Consider:")
            print(f"      - Using longer text excerpt")
            print(f"      - Checking if document has actual character dialogue")
        
        if len(result['characters']) > 10:
            print(f"   ℹ️  Many characters extracted. This is normal for:")
            print(f"      - Novels with large casts")
            print(f"      - Multi-POV stories")
            print(f"      - Epic fantasy/sci-fi")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_production_extraction.py <document_id>")
        print("\nExample:")
        print("  python test_production_extraction.py fa0d116d-38ca-4de5-9f2b-611ddcde9d2f")
        print("\nThis tests the production-grade extraction that filters out:")
        print("  • Insults/mockery (idiot, fool, princess)")
        print("  • Titles (lieutenant, captain, handler)")
        print("  • Groups (Eighty-Six, soldiers)")
        print("  • Epigraph authors")
        sys.exit(1)
    
    document_id = sys.argv[1]
    test_production_extraction(document_id)
