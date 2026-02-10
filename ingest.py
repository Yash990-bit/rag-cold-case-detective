import os

def ingest_evidence(directory):
    """
    Reads text files from a directory and returns a data structure 
    that separates content from source metadata.
    """
    evidence_data = []
    
    if not os.path.exists(directory):
        print(f"Error: Directory {directory} not found.")
        return evidence_data

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                evidence_data.append({
                    'content': content,
                    'source': filename
                })
    
    return evidence_data

if __name__ == "__main__":
    evidence_path = "evidence"
    loaded_data = ingest_evidence(evidence_path)
    
    print(f"--- Loaded {len(loaded_data)} evidence files ---")
    if loaded_data:
        # Milestone Check: Print one of the loaded data objects
        print("\n[Milestone Check] Sample Data Object:")
        import json
        print(json.dumps(loaded_data[0], indent=2))
