import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        timeout_keep_alive=120  # Increase timeout to 120 seconds for character extraction
    )