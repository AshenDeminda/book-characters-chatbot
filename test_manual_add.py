from src.api.main import app
from src.api.routes import chat

print(f"Before manual add: {len(app.routes)} routes")
print("Routes:", [r.path for r in app.routes if hasattr(r, 'path')])

print(f"\nChat router has: {len(chat.router.routes)} routes")
print("Chat routes:", [r.path for r in chat.router.routes])

# Manually try to include
print("\nTrying manual include_router...")
try:
    app.include_router(chat.router, prefix="/api/v1", tags=["chat_manual"])
    print(f"After manual add: {len(app.routes)} routes")
    print("Routes:", [r.path for r in app.routes if hasattr(r, 'path')])
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
