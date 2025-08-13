# app.py
import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai # Import the openai library
import requests
import os # Import the os library to read environment variables

# --- App Initialization ---
app = Flask(__name__)
CORS(app) 

# --- In-Memory Data Stores ---
knowledge_base = { "chunks": [], "embeddings": [], "file_name": None }

# --- Helper Functions for RAG ---
def chunk_text(text, chunk_size=500, overlap=50):
    """Splits text into smaller, overlapping chunks."""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def get_embedding(text, api_key):
    """Generates a vector embedding for a given text using OpenAI's API."""
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
    # Ensure your frontend HTML file is named 'index.html' in the 'templates' folder
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
        knowledge_base = { "chunks": chunks, "embeddings": [], "file_name": file.filename }
        return jsonify({ "message": f"File '{file.filename}' processed. {len(chunks)} chunks created." })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Main RAG endpoint for answering questions using OpenAI."""
    data = request.json
    
    # AWS DEPLOYMENT CHANGE: Prioritize environment variables for the API key
    api_key = os.environ.get('OPENAI_API_KEY') or data.get('api_key')
    
    query = data.get('query')
    if not query or not api_key: return jsonify({"error": "Query and API Key are required."}), 400
    if not knowledge_base["chunks"]: return jsonify({"error": "Please upload a knowledge file first."}), 400
    
    try:
        if not knowledge_base["embeddings"]:
            knowledge_base["embeddings"] = [get_embedding(chunk, api_key) for chunk in knowledge_base["chunks"]]
        
        query_embedding = get_embedding(query, api_key)
        similarities = [cosine_similarity(query_embedding, emb) for emb in knowledge_base["embeddings"]]
        top_indices = np.argsort(similarities)[-3:][::-1]
        context = "\n\n---\n\n".join([knowledge_base["chunks"][i] for i in top_indices])

        prompt = f"Based ONLY on the following context, answer the question.\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(model="gpt-4", messages=[{"role": "system", "content": prompt}])
        final_response = response.choices[0].message.content

        return jsonify({"response": final_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/automate', methods=['POST'])
def automate():
    """Custom Tool: Triggers an n8n workflow for complex automations."""
    data = request.json
    instruction = data.get('instruction')

    # AWS DEPLOYMENT CHANGE: Prioritize environment variables for the webhook URL
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
    
    # AWS DEPLOYMENT CHANGE: Prioritize environment variables for Strapi credentials
    strapi_url = os.environ.get('STRAPI_URL') or data.get('strapi_url')
    strapi_token = os.environ.get('STRAPI_TOKEN') or data.get('strapi_token')

    if not all([note_content, strapi_url, strapi_token]):
        return jsonify({"error": "Content, Strapi URL, and Strapi Token are required."}), 400

    headers = {
        'Authorization': f'Bearer {strapi_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'data': {
            'content': note_content
        }
    }

    try:
        response = requests.post(strapi_url, headers=headers, json=payload)
        response.raise_for_status() 
        
        response_data = response.json()
        strapi_id = response_data.get('data', {}).get('id')
        
        return jsonify({
            "response": f"Note saved successfully to Strapi with ID: {strapi_id}"
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to save note to Strapi: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
    