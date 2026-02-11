import os
import google.generativeai as genai
from dotenv import load_dotenv
from vector_store import blind_search

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Warning: GOOGLE_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=api_key)

def generate_response(query):
    """
    Retrieves evidence and generates a response using Gemini with strict citations.
    """
    # 1. Retrieve top 2-3 relevant documents
    results = blind_search(query, n_results=3)
    
    # 2. Format context for the prompt
    context_entries = []
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        context_entries.append(f"SOURCE: {meta['source']}\nCONTENT: {doc.strip()}")
    
    retrieved_documents = "\n\n".join(context_entries)
    
    # 3. Create Strong Prompt
    prompt = f"""
You are a detective assistant.
Answer ONLY using the context below.
Do not invent information.
Cite sources explicitly using their filenames.

Context:
{retrieved_documents}

Question:
{query}
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"

def extract_timeline():
    """
    Reads all text files in the evidence folder and uses Gemini to 
    extract a chronological timeline of events.
    """
    evidence_dir = "evidence"
    all_content = []
    
    if not os.path.exists(evidence_dir):
        return []

    for filename in os.listdir(evidence_dir):
        if filename.endswith(".txt"):
            with open(os.path.join(evidence_dir, filename), 'r') as f:
                all_content.append(f"Source: {filename}\nContent: {f.read()}")

    context_text = "\n\n---\n\n".join(all_content)
    
    prompt = f"""
    Review the following cold case evidence and extract a chronological timeline of events.
    For each event, provide:
    1. A precise timestamp/date (as mentioned in the text).
    2. A brief description of the event.
    3. The source file name.
    
    EVIDENCE:
    {context_text}
    
    Format your response as a valid JSON list of objects like this:
    [
      {{"time": "2023-10-14 21:00", "event": "Man in dark hoodie seen running", "source": "witness_sarah.txt"}},
      ...
    ]
    Sort the events from oldest to newest. Return ONLY the JSON.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        # Clean potential markdown wrapping
        json_text = response.text.strip().replace('```json', '').replace('```', '')
        import json
        return json.loads(json_text)
    except Exception as e:
        print(f"Error extracting timeline: {e}")
        return []

def main():
    print("--- Cold Case Detective RAG Pipeline ---")
    print("Ask a question about the case (type 'exit' to quit).\n")
    
    while True:
        user_input = input("Question: ")
        if user_input.lower() == 'exit':
            break
            
        print("\nDetective is reviewing evidence...")
        answer = generate_response(user_input)
        print(f"\nFinal Answer: {answer}\n")

if __name__ == "__main__":
    # For testing the specific requirement:
    # Query: "What evidence confirms the car color?"
    print("Testing specific query: 'What evidence confirms the car color?'")
    test_answer = generate_response("What evidence confirms the car color?")
    print(f"Answer: {test_answer}\n")
    
    # Uncomment to run the interactive loop
    # main()
