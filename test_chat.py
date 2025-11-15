"""
Test script for character chat with RAG
Usage: python test_chat.py <document_id> <character_id>
"""
import sys
import requests
import json

def test_character_chat(document_id: str, character_id: str):
    """Test chatting with a character"""
    base_url = "http://localhost:8000/api/v1"
    
    print("="*80)
    print("🤖 CHARACTER CHAT TEST (with RAG)")
    print("="*80)
    
    # Step 1: Get character greeting
    print(f"\n📝 Step 1: Getting greeting from character...")
    greeting_url = f"{base_url}/chat/greeting"
    greeting_payload = {
        "document_id": document_id,
        "character_id": character_id
    }
    
    try:
        response = requests.post(greeting_url, json=greeting_payload)
        response.raise_for_status()
        greeting_result = response.json()
        
        character_name = greeting_result['character_name']
        greeting = greeting_result['greeting']
        
        print(f"\n✅ {character_name}: {greeting}\n")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting greeting: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)
    
    # Step 2: Start conversation
    print("="*80)
    print("💬 CONVERSATION (type 'quit' to exit)")
    print("="*80)
    
    conversation_history = []
    chat_url = f"{base_url}/chat"
    
    while True:
        # Get user input
        user_message = input(f"\nYou: ").strip()
        
        if not user_message:
            continue
        
        if user_message.lower() in ['quit', 'exit', 'bye']:
            print(f"\n{character_name}: Goodbye!")
            break
        
        # Prepare chat request
        chat_payload = {
            "document_id": document_id,
            "character_id": character_id,
            "message": user_message,
            "conversation_history": conversation_history
        }
        
        try:
            print(f"\n{character_name} is thinking... (using RAG)")
            response = requests.post(chat_url, json=chat_payload)
            response.raise_for_status()
            chat_result = response.json()
            
            character_response = chat_result['response']
            context_used = chat_result['context_chunks_used']
            
            print(f"\n{character_name}: {character_response}")
            print(f"\n[ℹ️  Used {context_used} story chunks for context]")
            
            # Show relevant context (optional)
            if chat_result.get('relevant_context'):
                print(f"\n[📚 Relevant story context:")
                for i, ctx in enumerate(chat_result['relevant_context'], 1):
                    relevance = ctx.get('relevance_score')
                    if relevance:
                        print(f"   {i}. Relevance: {relevance:.2%}")
                    print(f"      \"{ctx['text']}\"")
                print("]")
            
            # Update conversation history
            conversation_history.append({
                "role": "user",
                "content": user_message
            })
            conversation_history.append({
                "role": "assistant",
                "content": character_response
            })
            
            # Keep only last 10 messages
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            continue
    
    # Save conversation
    output_file = f"conversation_{document_id}_{character_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "document_id": document_id,
            "character_id": character_id,
            "character_name": character_name,
            "conversation": conversation_history
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Conversation saved to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_chat.py <document_id> <character_id>")
        print("\nExample:")
        print("  python test_chat.py fa0d116d-38ca-4de5-9f2b-611ddcde9d2f char_shinei_nouzen")
        print("\nFirst, extract characters to get character_id:")
        print("  python test_characters.py <document_id>")
        sys.exit(1)
    
    document_id = sys.argv[1]
    character_id = sys.argv[2]
    test_character_chat(document_id, character_id)
