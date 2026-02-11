

from ingest import ingest_evidence
import os
import pickle

# Global variable for the model, initially None
_model = None

def get_model():
    """
    Lazy loads the SentenceTransformer model.
    """
    global _model
    if _model is None:
        print("Loading embedding model...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def build_vector_store(evidence_data, store_path="vector_store.pkl"):
    """
    Embeds evidence text and stores it in a FAISS index with metadata.
    """
    documents = [item['content'] for item in evidence_data]
    metadatas = [{"source": item['source']} for item in evidence_data]
    
    # Create embeddings
    model = get_model()
    import numpy as np
    embeddings = model.encode(documents)
    embeddings = np.array(embeddings).astype('float32')
    
    # Initialize FAISS index
    import faiss
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # Save index and metadata
    with open(store_path, "wb") as f:
        pickle.dump({"index": index, "metadatas": metadatas, "documents": documents}, f)
    
    return index

def blind_search(query, n_results=1, store_path="vector_store.pkl"):
    """
    Performs a similarity search using FAISS.
    """
    if not os.path.exists(store_path):
        print("Error: Vector store not found. Please build it first.")
        return {"documents": [[]], "metadatas": [[]]}
        
    with open(store_path, "rb") as f:
        data = pickle.load(f)
        index = data["index"]
        metadatas = data["metadatas"]
        documents = data["documents"]
    
    # Embed query
    model = get_model()
    import numpy as np
    query_embedding = model.encode([query]).astype('float32')
    
    # Search
    distances, indices = index.search(query_embedding, n_results)
    
    # Format results to mimic ChromaDB structure for compatibility
    res_docs = []
    res_metas = []
    for idx in indices[0]:
        if idx != -1:
            res_docs.append(documents[idx])
            res_metas.append(metadatas[idx])
            
    return {"documents": [res_docs], "metadatas": [res_metas]}

if __name__ == "__main__":
    # 1. Load data from Phase 1
    evidence_path = "evidence"
    data = ingest_evidence(evidence_path)
    
    # 2. Build the store
    print("Building vector store (FAISS)...")
    build_vector_store(data)
    
    # 3. [Milestone Check] The "Blind" Search
    query = "What color was the car?"
    print(f"\n[Milestone Check] Performing Blind Search for: '{query}'")
    
    # Perform vector search
    results = blind_search(query)
    
    # Print result in requested format
    print("\n--- Similarity Search Result ---")
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        print(f"Source: {meta['source']}")
        print(f"Content: {doc.strip()}")
