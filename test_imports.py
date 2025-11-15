import sys
import traceback

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Testing imports...")

try:
    print("\n1. Testing RAG service...")
    from src.rag.rag_service import RAGService
    print("OK - RAGService imported")
    
    print("\n2. Testing Chat service...")
    from src.services.chat_service import ChatService
    print("OK - ChatService imported")
    
    print("\n3. Testing chat routes...")
    from src.api.routes import chat
    print(f"OK - Chat module imported")
    print(f"  Router: {chat.router}")
    print(f"  Routes: {[r.path for r in chat.router.routes]}")
    
    print("\n4. Testing main app...")
    from src.api.main import app
    print(f"OK - Main app imported")
    print(f"  Total routes: {len(app.routes)}")
    
    # List all routes
    print("\n5. All registered routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"  {list(route.methods)} {route.path}")
    
    print("\nSUCCESS - ALL IMPORTS SUCCESSFUL!")
    
except Exception as e:
    print(f"\nERROR:")
    traceback.print_exc()
