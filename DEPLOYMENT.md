# Deployment Guide

Follow these steps to deploy your Chemical Visualizer to the web for free.

## Phase 1: Push Changes
First, make sure the latest changes (Deployment config) are on GitHub.
```bash
git add .
git commit -m "Configure for deployment"
git push origin main
```

---

## Phase 2: Deploy Backend (Render.com)
1.  **Sign Up/Login** at [render.com](https://render.com).
2.  Click **New +** -> **Web Service**.
3.  Connect your GitHub repository.
4.  **Configuration**:
    *   **Name**: `chemical-backend` (or similar)
    *   **Root Directory**: `backend` (Important!)
    *   **Runtime**: Python 3
    *   **Build Command**: `./build.sh`
    *   **Start Command**: `gunicorn chemical_project.wsgi:application`
5.  **Environment Variables** (Scroll down to "Advanced"):
    *   Key: `PYTHON_VERSION` | Value: `3.9.0` (or 3.11.0)
    *   Key: `SECRET_KEY` | Value: `(Generate a random string here)`
    *   Key: `RENDER` | Value: `true`
    *   Key: `RENDER_EXTERNAL_HOSTNAME` | Value: `(Leave empty for now, or put your vercel URL later)`
6.  Click **Create Web Service**.
7.  **Wait**: It will take a few minutes. Once live, copy the URL (e.g., `https://chemical-backend.onrender.com`).

---

## Phase 3: Deploy Frontend (Vercel)
1.  **Sign Up/Login** at [vercel.com](https://vercel.com).
2.  Click **Add New...** -> **Project**.
3.  Import your GitHub repository.
4.  **Configuration**:
    *   **Framework Preset**: Vite (It should auto-detect).
    *   **Root Directory**: Click "Edit" and select `web`.
5.  **Environment Variables**:
    *   Key: `VITE_API_URL`
    *   Value: `https://chemical-backend.onrender.com` (The URL you copied from Render)
    *   *Note: Do not add a trailing slash `/` at the end.*
6.  Click **Deploy**.

## Phase 4: Final Connection
1.  Once Vercel finishes, you will get a frontend URL (e.g., `https://chemical-visualizer.vercel.app`).
2.  Go back to **Render Dashboard** -> **Environment**.
3.  Add/Edit Variable:
    *   Key: `RENDER_EXTERNAL_HOSTNAME`
    *   Value: `chemical-visualizer.vercel.app` (Your Vercel domain without https://)
4.  This adds your frontend to the `ALLOWED_HOSTS` list in Django.

## Done! 🚀
Open your Vercel URL. You should be able to upload CSVs and see charts just like on your local machine.
