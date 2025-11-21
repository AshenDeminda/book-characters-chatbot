from src.models.database import SessionLocal, Base, engine
from src.models.chat_session import ChatSession
from src.services.chat_session_service import ChatSessionService

# Ensure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()
print('Existing chat_sessions count before test:', db.query(ChatSession).count())
for s in db.query(ChatSession).all():
    print(' -', s.session_id, 'messages:', s.get_messages())

# Insert a test chat (default_ prefix to match save logic)
try:
    session = ChatSessionService.save_message(
        db=db,
        document_id='default_testdoc',
        character_id='char_test',
        character_name='Test Character',
        user_message='Hello test',
        assistant_response='Hi test'
    )
    print('Inserted/Updated session:', session.session_id)
except Exception as e:
    print('Error when saving test session:', e)

print('Existing chat_sessions count after test:', db.query(ChatSession).count())
for s in db.query(ChatSession).all():
    print(' -', s.session_id, 'messages:', s.get_messages())

db.close()
