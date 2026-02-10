import chromadb
from chromadb.utils import embedding_functions
from ingest import ingest_evidence
import os

# Initialize the embedding function (using a small, efficient model)
# This will download the model on the first run
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def build_vector_store(evidence_data):
    """
    Creates a ChromaDB collection, embeds evidence text, 
    and stores it along with source metadata.
    """
    # Persistent storage in the current directory
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Create or get collection
    # We'll call it "cold_case_evidence"
    collection = client.get_or_create_collection(
        name="cold_case_evidence",
        embedding_function=embedding_func
    )
    
    # Prepare data for Chroma
    documents = []
    metadatas = []
    ids = []
    
    for i, item in enumerate(evidence_data):
        documents.append(item['content'])
        metadatas.append({"source": item['source']})
        ids.append(f"doc_{i}")
    
    # Add to collection
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    return collection

def blind_search(query, n_results=1):
    """
    Performs a similarity search without an LLM.
    """
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(
        name="cold_case_evidence",
        embedding_function=embedding_func
    )
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    return results

if __name__ == "__main__":
    # 1. Load data from Phase 1
    evidence_path = "evidence"
    data = ingest_evidence(evidence_path)
    
    # 2. Build the store
    print("Building vector store...")
    build_vector_store(data)
    
    # 3. [Milestone Check] The "Blind" Search
    query = "What color was the car?"
    print(f"\n[Milestone Check] Performing Blind Search for: '{query}'")
    
    raw_results = blind_search(query)
    
    # Verify the structure is what we expect
    print("\n--- Similarity Search Result ---")
    results = blind_search(query)
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        print(f"Source: {meta['source']}")
        print(f"Text: {doc}")
