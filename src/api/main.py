from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from src.models.database import engine, get_db, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Book Characters Chatbot API")

@app.get("/")
def read_root():
    return {"message": "Book Characters Chatbot API", "status": "running"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database": "connected"}