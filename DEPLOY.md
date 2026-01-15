# 🚀 Free Deployment Guide

Since this is a full-stack application with a Python backend (FastAPI) and a React frontend, we will use two specialized free-tier services:
1.  **Render**: For the backend (Python support, 50s+ timeout tolerance for AI).
2.  **Vercel**: For the frontend (Optimized for React/Vite).

---

## Part 1: Deploy Backend (Render)

1.  Go to [dashboard.render.com](https://dashboard.render.com/) and create a free account.
2.  Click **"New +"** → **"Web Service"**.
3.  Select **"Build and deploy from a Git repository"** and connect your GitHub account.
4.  Select `trainsmarter` from your list of repos.
5.  Configure the service:
    *   **Name**: `trainsmarter-api` (or similar)
    *   **Region**: Choose closest to you (e.g., US East)
    *   **Root Directory**: `backend`  (⚠️ Important!)
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 10000`
    *   **Instance Type**: `Free`
6.  **Environment Variables** (Click "Advanced"):
    *   Add `ANTHROPIC_API_KEY`: *(Paste your key)*
    *   Add `RAPIDAPI_KEY`: *(Paste your key)*
7.  Click **"Create Web Service"**.
8.  **Wait**: It will take a few minutes. Once live, copy the URL (e.g., `https://trainsmarter-api.onrender.com`).

---

## Part 2: Deploy Frontend (Vercel)

1.  Go to [vercel.com](https://vercel.com/) and sign up with GitHub.
2.  Click **"Add New..."** → **"Project"**.
3.  Import the `trainsmarter` repository.
4.  Configure the project:
    *   **Framework Preset**: Vite (should detect automatically)
    *   **Root Directory**: `.` (Default is fine)
5.  **Environment Variables**:
    *   Key: `VITE_API_URL`
    *   Value: `https://trainsmarter-api.onrender.com/api`  (⚠️ Paste your Render URL + `/api`)
6.  Click **"Deploy"**.

---

## 🎉 Done!

Your app will be live at the Vercel URL! 

> **Note**: The Render free tier spins down after inactivity. The first request might take ~50 seconds to wake up the server. This is normal for the free tier.
