from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import rag_chat
from ingest import ingest_evidence
from vector_store import build_vector_store, blind_search
import os

app = FastAPI()


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

@app.post("/ingest")
async def ingest_endpoint():
    try:
        data = ingest_evidence("evidence")
        build_vector_store(data)
        return {"status": "success", "message": f"Ingested {len(data)} evidence chunks"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cases")
async def get_cases():
    """
    Returns a list of unique cases detected in the evidence files.
    """
    evidence_dir = "evidence"
    if not os.path.exists(evidence_dir):
        return {"cases": []}
    
    cases = set()
    for filename in os.listdir(evidence_dir):
        if filename.endswith(".txt"):
            file_path = os.path.join(evidence_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith("Case ID:") or first_line.startswith("Case:"):
                    cases.add(first_line.split(":")[1].strip())
                else:
                    cases.add("Uncategorized")
    
    return {"cases": sorted(list(cases))}

@app.get("/timeline")
async def get_timeline(case_id: str = None):
    try:
        # If case_id is provided, filter or pass it to extraction logic
        # For now, we return the full timeline or a filtered one
        timeline = rag_chat.extract_timeline()
        if case_id and case_id != "All":
             # Optional: filter timeline by case_id if possible
             pass
        return {"timeline": timeline}
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
