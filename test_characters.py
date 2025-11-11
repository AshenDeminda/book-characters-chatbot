"""
Test script for character extraction API
Usage: python test_characters.py <document_id>
"""
import requests
import sys
import json

def extract_characters(document_id: str, max_characters: int = 10):
    """Test character extraction endpoint"""
    url = "http://localhost:8000/api/v1/characters/extract-characters"
    
    payload = {
        "document_id": document_id,
        "max_characters": max_characters
    }
    
    print(f"\n🔍 Extracting characters from document: {document_id}")
    print(f"   Max characters to find: {max_characters}")
    print(f"   Endpoint: {url}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Characters extracted successfully!\n")
            print(f"📊 Total characters found: {data['total_found']}\n")
            
            print("=" * 80)
            for i, char in enumerate(data['characters'], 1):
                print(f"\n{i}. {char['name']}")
                print(f"   ID: {char['character_id']}")
                print(f"   Role: {char['role']}")
                print(f"   Description: {char['description']}")
                print("-" * 80)
            
            # Save to file
            output_file = f"characters_{document_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {output_file}")
            
        else:
            print(f"❌ Request failed!")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.json()}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out! Character extraction may take a while with large documents.")
        print("   Try reducing max_characters or wait longer.")
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Is the server running on http://localhost:8000?")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_characters.py <document_id> [max_characters]")
        print("\nExample:")
        print("  python test_characters.py 2013e04b-50fd-40a2-92c8-c8723b207370")
        print("  python test_characters.py 2013e04b-50fd-40a2-92c8-c8723b207370 15")
        sys.exit(1)
    
    doc_id = sys.argv[1]
    max_chars = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    extract_characters(doc_id, max_chars)
