# ... (Keep previous imports)
import os
import google.generativeai as genai
from vector_store import blind_search

# Configure the Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Warning: GOOGLE_API_KEY not found in environment variables.")
else:
    genai.configure(api_key=api_key)

# Global memory to store the conversation history
# Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
conversation_history = []

def generate_response(query):
    """
    Retrieves evidence, constructs a prompt with history, and generates a response using Gemini.
    """
    # 1. Retrieve the most relevant evidence
    # We might want to use the history to refine the search, but for now, 
    # we'll stick to the current query for retrieval.
    results = blind_search(query, n_results=3)
    
    # 2. Extract content and metadata
    context_entries = []
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        context_entries.append(f"Source: {meta['source']}\nContent: {doc}")
    
    context_text = "\n\n---\n\n".join(context_entries)
    
    # 3. Format Conversation History for the prompt
    history_text = ""
    for entry in conversation_history[-5:]: # Keep last 5 exchanges
        role = "User" if entry['role'] == "user" else "Assistant"
        history_text += f"{role}: {entry['content']}\n"
    
    # 4. Construct the prompt
    prompt = f"""
    You are a Cold Case Detective assistant. Your goal is to answer questions about a case based strictly on the evidence provided below and the conversation history.
    
    RULES:
    1. Only use information provided in the Evidence section.
    2. If the answer isn't in the evidence, say "I don't have enough evidence to answer that."
    3. You MUST cite the source file (e.g., [police_log.txt]) for every piece of information.
    4. Use the Conversation History to understand follow-up questions (e.g., "What did she see?" when referring to a witness mentioned earlier).
    
    CONVERSATION HISTORY:
    {history_text}
    
    EVIDENCE:
    {context_text}
    
    NEW QUESTION: {query}
    
    DETECTIVE'S RESPONSE:
    """
    
    # 5. Generate response using Gemini
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        answer = response.text.strip()
        
        # Update history
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": answer})
        
        return answer
    except Exception as e:
        return f"Error connecting to Gemini API: {e}"

def chat_loop():
    print("--- Cold Case Detective Chatbot (With Memory) ---")
    print("Type 'exit' or 'quit' to stop.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        print("\nDetective is reviewing files and history...")
        response = generate_response(user_input)
        print(f"\nDetective: {response}\n")

if __name__ == "__main__":
    chat_loop()
