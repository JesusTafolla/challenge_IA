# aws_deploy.md: Detailed AWS Deployment Guide

This document provides a complete, step-by-step guide for deploying your AI Assistant project to a production-ready environment using AWS Elastic Beanstalk, with detailed explanations for each step.

---

## 1. Deploy Your Strapi CMS

**Why do this first?** Your main AI application will be running on an AWS server on the public internet. It cannot connect to a `localhost` address on your computer. Therefore, your Strapi CMS must *also* be deployed to a public URL so the AWS server can communicate with it.

#### **Step 1: Create a Production-Ready Database**

Strapi's default local database (SQLite) is not suitable for production. You need a cloud-based PostgreSQL database.

1.  Sign up for a free account at a service like **Neon** ([neon.tech](https://neon.tech)).
2.  Create a new project.
3.  On your project dashboard, find the **Connection Details** and copy the **connection URL** (it will start with `postgres://...`).

#### **Step 2: Push Strapi to GitHub**

Cloud deployment services work by pulling code from a Git repository.

1.  Create a new, empty repository on GitHub (e.g., `my-strapi-cms`).
2.  In your local `my-strapi-project` folder, run the necessary `git` commands to push your code to this new repository.

#### **Step 3: Deploy Strapi to a Cloud Service (e.g., Render)**

1.  Sign up for a free account on **Render** ([render.com](https://render.com)).
2.  Create a **New Web Service** and connect your Strapi GitHub repository.
3.  **Configuration**:
    * **Name**: A unique name (e.g., `my-ai-strapi-cms`).
    * **Build Command**: `npm install && npm run build`
    * **Start Command**: `npm start`
    * **Instance Type**: Free
4.  **Environment Variables**: This is the most critical part. Add the following environment variables:
    * `NODE_ENV`: `production` (Tells Strapi to run in production mode).
    * `DATABASE_URL`: The PostgreSQL connection URL you copied from Neon.
    * `JWT_SECRET`, `ADMIN_JWT_SECRET`, `API_TOKEN_SALT`: Click the "Generate" button next to each value field. These are random, secure keys that Strapi needs to function correctly.
5.  Click **Create Web Service**. After a few minutes, your Strapi instance will be live at a public URL (e.g., `https://my-ai-strapi-cms.onrender.com`).

---

## 2. Deploy the AI Assistant to AWS

#### **Prerequisites**

* An AWS Account.
* The AWS CLI installed and configured (`aws configure`).
* The EB CLI installed (`pip install awsebcli`).

#### **Prepare for Deployment**

1.  In your AI Assistant project's root directory, create a folder named `.ebextensions`.
2.  Inside it, create a file named `python.config` with the following content. This tells the AWS server how to run a Flask application.
    ```
    option_settings:
      aws:elasticbeanstalk:container:python:
        WSGIPath: app:app
    ```

#### **Deploy from Your Terminal**

1.  Navigate to your project's root directory.
2.  **Initialize**: `eb init -p python-3.9 activamente-challenge --region us-east-1`
3.  **Create Environment**: `eb create --sample activamente-env` (This will take several minutes).
4.  **Deploy Updates**: `eb deploy`
5.  **Open App**: `eb open`

---

## 3. Final Configuration: Environment Variables

For security, all your secret keys and URLs must be stored as environment variables on the AWS server, not in your code. The backend is already configured to read these.

1.  Go to your **AWS Elastic Beanstalk Console**.
2.  Navigate to your environment's **Configuration -> Software -> Edit** page.
3.  Scroll down to **Environment properties** and add the following:
    * `OPENAI_API_KEY`: Your secret OpenAI key.
    * `CLAUDE_API_KEY`: Your secret Claude key.
    * `STRAPI_URL`: Your **public Render URL** for Strapi, with `/api/notes` at the end (e.g., `https://my-strapi-cms.onrender.com/api/notes`).
    * `STRAPI_TOKEN`: The API token for your **deployed** Strapi app (you may need to create a new token in your live Strapi instance).
    * `N8N_WEBHOOK_URL`: The **Production URL** from your n8n Webhook node.

Your application is now fully deployed and securely configured on AWS.