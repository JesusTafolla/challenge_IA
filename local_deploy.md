# local_deploy.md: Detailed Local Setup Guide

This document provides a complete, step-by-step guide to setting up and running the entire AI Assistant project on your local machine for development and testing, with detailed explanations for each service.

---

## 1. Prerequisites

Before you begin, ensure you have the following software installed on your computer:
-   **Node.js** (LTS version recommended)
-   **Python** (Version 3.8 or newer)
-   **Git**
-   **ngrok** (Downloaded and authenticated with your account)

---

## 2. Project Setup

1.  **Folder Structure**:
    Organize your project folder exactly like this:
    ```
    /activamente-challenge
    |-- app.py
    |-- requirements.txt
    |-- /templates
        |-- index.html
    ```

2.  **`requirements.txt` File**:
    This file must contain:
    ```
    flask
    flask-cors
    openai
    anthropic
    numpy
    requests
    ```

3.  **Python Environment**:
    * Open a terminal and navigate to your project folder.
    * Create a virtual environment: `py -m venv venv`
    * Activate it: `venv\Scripts\activate`
    * Install dependencies: `pip install -r requirements.txt`

---

## 3. Running All Services (Order is Important)

You will need to have **three separate terminal windows** open and running at the same time.

#### **Terminal 1: Start Strapi**

1.  Navigate to your Strapi project folder (`my-strapi-project`).
2.  Run the following command to start the server and allow external connections from ngrok:
    ```bash
    npm run develop -- --host=0.0.0.0
    ```
    * **Why `--host=0.0.0.0`?** By default, Strapi only listens for connections from `localhost` (your own computer). This command tells Strapi to listen for connections from **any network address**, which is crucial for allowing the `ngrok` tunnel to connect to it from the outside.
3.  **Keep this terminal open.**

#### **Terminal 2: Start ngrok**

1.  Open a new terminal.
2.  Run the following command to create a public tunnel to your Strapi server on port 1337:
    ```bash
    ngrok http 1337
    ```
    * This tells ngrok to forward all public traffic it receives to port `1337` on your local machine, which is where Strapi is running.
3.  Look for the `Forwarding` line in the ngrok output and **copy the `https` URL**. It will look like `https://random-string.ngrok-free.app`.
4.  **Keep this terminal open.**

#### **Terminal 3: Start the AI Assistant Backend**

1.  Open a third terminal.
2.  Navigate to your AI Assistant project folder.
3.  Activate the virtual environment: `venv\Scripts\activate`
4.  Run the Flask server:
    ```bash
    python app.py
    ```
5.  **Keep this terminal open.**

---

## 4. Final Configuration (Strapi & n8n)

With all servers running, you need to configure the services to talk to each other.

#### **Configure n8n Workflow**

1.  Log in to your n8n account and open your workflow.
2.  **Webhook Node**: Ensure the "HTTP Method" is set to **POST**. Copy the **Test URL**.
3.  **Strapi Node**:
    * **Credentials**: Edit your Strapi credential. The **Base URL** must be the **ngrok URL** you copied (e.g., `https://random-string.ngrok-free.app`). Do **NOT** add `/api/notes` to this URL.
    * **Configuration**: Set Resource to `Entry`, Content Type to `Note`, and Operation to `Create`.
    * **Data Mapping**: Map the `instruction` from the webhook to the `content` field.
    * **Activate** your workflow.

#### **Configure the AI Assistant UI**

1.  Open `http://127.0.0.1:5001` in your web browser.
2.  Enter the following:
    * **API Key**: Your OpenAI or Claude API key.
    * **n8n Webhook URL**: The **Test URL** from your n8n Webhook node.
    * **Strapi API URL**: Your **local** Strapi URL: `http://localhost:1337/api/notes`.
    * **Strapi API Token**: Your Strapi token.

Your entire system is now running and correctly configured for local development.