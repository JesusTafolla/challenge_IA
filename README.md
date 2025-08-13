ActivaMente AI Challenge Project
This project is a complete implementation of the ActivaMente AI Challenge. It's a Python-based web application that serves as an AI Knowledge Assistant using Retrieval-Augmented Generation (RAG). The application is designed to be flexible, scalable, and ready for both local development and cloud deployment.

✨ Features
Multi-LLM Support: Dynamically switch between OpenAI (GPT-4) and Anthropic (Claude) models for generating responses.

RAG Pipeline: Upload a .txt file to create a custom knowledge base. The assistant will use this document to provide factual, context-aware answers, minimizing hallucinations.

Dual Tool Integration: The assistant is equipped with two types of tools to demonstrate different integration patterns:

Direct Tool (save note:): A command to save a note directly to a Strapi CMS via a REST API call.

Automation Tool (automate:): A more advanced command that triggers a flexible n8n.io workflow via a webhook, allowing for complex, multi-step automations.

Deployment Ready: The application is configured for both local development and deployment to AWS Elastic Beanstalk, with secure handling of API keys and credentials via environment variables.

🚀 Getting Started: Running Locally
To run this project on your local machine, you will need to have three services running simultaneously: the main Python application, a Strapi CMS instance, and an ngrok tunnel.

Prerequisites
Node.js (LTS)

Python (3.8+)

An n8n account (cloud or local)

ngrok

1. Set Up and Run Strapi
First, set up and run your Strapi instance. This will act as the database for your tools.

# In a new terminal, navigate to your Strapi project folder
npm run develop -- --host=0.0.0.0

2. Set Up and Run ngrok
Next, create a public tunnel to your local Strapi server so n8n.cloud can access it.

# In a second terminal
ngrok http 1337

Copy the https URL provided by ngrok.

3. Set Up and Run the AI Assistant
Finally, run the main Python application.

# In a third terminal, navigate to this project's folder

# Create and activate a virtual environment
py -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py

4. Configure and Use
Open your browser to http://127.0.0.1:5001.

Configure your n8n workflow to use the ngrok URL as the Base URL for its Strapi credential.

In the application UI, enter your API keys, your local Strapi URL (http://localhost:1337/api/notes), your Strapi token, and your n8n webhook URL.

Upload a .txt file and start asking questions!

☁️ Deployment
For detailed instructions on how to deploy this application to a live, production-ready environment on AWS, please refer to the DEPLOY_AWS.md guide.