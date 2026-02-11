from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import rag_chat
from vector_store import blind_search
import os

app = FastAPI()

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: list

@app.get("/")
def read_root():
    return {"status": "Detective API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "api_key_set": bool(os.getenv("GOOGLE_API_KEY"))}

@app.get("/timeline")
async def get_timeline():
    try:
        events = rag_chat.extract_timeline()
        return {"timeline": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Get response using the logic in rag_chat.py
        response_text = rag_chat.generate_response(request.message)
        
        # Determine if it's an error message or a real response
        # If it's an error, we still want to show it in the chat
        
        # Get raw sources for the Case Board
        results = blind_search(request.message, n_results=3)
        sources = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            sources.append({
                "source": meta['source'],
                "content": doc
            })
            
        return ChatResponse(response=response_text, sources=sources)
    except Exception as e:
        # Instead of 500, return a clear message in the chat
        return ChatResponse(
            response=f"SYSTEM ERROR: {str(e)}",
            sources=[]
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
