from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chatbot
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

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Get response using the logic in chatbot.py
        # chatbot.generate_response handles history internally (for the terminal loop),
        # but for the API, we'll keep it simple for now or extend chatbot.py to be more modular.
        response_text = chatbot.generate_response(request.message)
        
        # We also want to provide the raw sources for the Case Board
        results = blind_search(request.message, n_results=3)
        sources = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            sources.append({
                "source": meta['source'],
                "content": doc
            })
            
        return ChatResponse(response=response_text, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
