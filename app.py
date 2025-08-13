# app.py
import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
import anthropic
import requests
import os # Import the os library to read environment variables

# --- App Initialization ---
app = Flask(__name__)
CORS(app) 

# --- In-Memory Data Stores ---
knowledge_base = { "chunks": [], "embeddings": {}, "file_name": None }

# --- Helper Functions ---
def chunk_text(text, chunk_size=500, overlap=50):
    """Splits text into smaller, overlapping chunks."""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def get_embedding(text, api_key):
    """Generates embeddings using OpenAI's model."""
    client = openai.OpenAI(api_key=api_key)
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding

def cosine_similarity(vec_a, vec_b):
    """Calculates cosine similarity to find relevant text chunks."""
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

# --- API Endpoints ---
@app.route('/')
def index():
    """Serves the main frontend file."""
    return render_template('index.html') 

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload and resets the knowledge base."""
    if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400
    try:
        text = file.read().decode('utf-8')
        chunks = chunk_text(text)
        global knowledge_base
        knowledge_base = { "chunks": chunks, "embeddings": {}, "file_name": file.filename }
        return jsonify({ "message": f"File '{file.filename}' processed. {len(chunks)} chunks created." })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Main RAG endpoint, supporting OpenAI and Claude."""
    data = request.json
    query = data.get('query')
    provider = data.get('provider', 'openai')
    
    # --- AWS DEPLOYMENT CHANGE ---
    # This logic first checks for environment variables set in AWS.
    # If it's running locally and they don't exist, it uses the key from the UI.
    openai_api_key = os.environ.get('OPENAI_API_KEY') or data.get('api_key')
    claude_api_key = os.environ.get('CLAUDE_API_KEY') or data.get('api_key')
    
    # Use the correct key for the selected provider
    llm_api_key = claude_api_key if provider == 'claude' else openai_api_key

    if not all([query, llm_api_key, provider]): return jsonify({"error": "Query, API Key, and Provider are required."}), 400
    if not knowledge_base["chunks"]: return jsonify({"error": "Please upload a knowledge file first."}), 400
    
    try:
        # Embeddings are always created with OpenAI for consistency
        if not knowledge_base["embeddings"]:
            knowledge_base["embeddings"] = [get_embedding(chunk, openai_api_key) for chunk in knowledge_base["chunks"]]
        
        query_embedding = get_embedding(query, openai_api_key)
        similarities = [cosine_similarity(query_embedding, emb) for emb in knowledge_base["embeddings"]]
        top_indices = np.argsort(similarities)[-3:][::-1]
        context = "\n\n---\n\n".join([knowledge_base["chunks"][i] for i in top_indices])

        prompt = f"Based ONLY on the following context, answer the question.\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        
        if provider == 'claude':
            client = anthropic.Anthropic(api_key=llm_api_key)
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            final_response = response.content[0].text
        elif provider == 'openai':
            client = openai.OpenAI(api_key=llm_api_key)
            response = client.chat.completions.create(model="gpt-4", messages=[{"role": "system", "content": prompt}])
            final_response = response.choices[0].message.content
        else:
            raise ValueError("Unsupported provider")

        return jsonify({"response": final_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/automate', methods=['POST'])
def automate():
    """Custom Tool: Triggers an n8n workflow for complex automations."""
    data = request.json
    instruction = data.get('instruction')
    
    # --- AWS DEPLOYMENT CHANGE ---
    n8n_webhook = os.environ.get('N8N_WEBHOOK_URL') or data.get('n8n_webhook')
    
    if not all([instruction, n8n_webhook]): return jsonify({"error": "Instruction and n8n Webhook URL are required."}), 400
    payload = {'instruction': instruction}
    try:
        response = requests.post(n8n_webhook, json=payload)
        response.raise_for_status() 
        n8n_response = response.json().get('message', 'Workflow triggered successfully!')
        return jsonify({"response": f"Automation sent to n8n: {n8n_response}"})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to trigger n8n workflow: {e}"}), 500

@app.route('/save-note', methods=['POST'])
def save_note():
    """Custom Tool: Saves a note directly to a Strapi CMS."""
    data = request.json
    note_content = data.get('content')

    # --- AWS DEPLOYMENT CHANGE ---
    strapi_url = os.environ.get('STRAPI_URL') or data.get('strapi_url')
    strapi_token = os.environ.get('STRAPI_TOKEN') or data.get('strapi_token')

    if not all([note_content, strapi_url, strapi_token]): return jsonify({"error": "Content, Strapi URL, and Strapi Token are required."}), 400
    headers = {'Authorization': f'Bearer {strapi_token}', 'Content-Type': 'application/json'}
    payload = {'data': {'content': note_content}}
    try:
        response = requests.post(strapi_url, headers=headers, json=payload)
        response.raise_for_status() 
        response_data = response.json()
        strapi_id = response_data.get('data', {}).get('id')
        return jsonify({"response": f"Note saved successfully to Strapi with ID: {strapi_id}"})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to save note to Strapi: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)