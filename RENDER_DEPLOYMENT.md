# 🚀 Deploy AI Career Coach on Render

Yeh guide aapko `tushar-kumar-code/ai-career-coach` repository ko **Render** par deploy karne ke complete steps batati hai.

---

## ⚡ Option 1: Render Blueprints (Recommended - 1-Click Auto Setup)

Humne repository ke root me [`render.yaml`](./render.yaml) file add kar di hai jo **Backend (FastAPI)** aur **Frontend (Next.js)** dono services ko automatically configure aur connect kar degi.

### Steps:
1. **Render Dashboard par jayein:**
   - [https://dashboard.render.com](https://dashboard.render.com) par jayein aur **"Log in with GitHub"** par click karein (`tushar-kumar-code` account se).

2. **Blueprint Create karein:**
   - Top right corner par **"New +"** button par click karein.
   - Dropdown menu se **"Blueprint"** select karein.
   - Apni repository **`tushar-kumar-code/ai-career-coach`** select karein (agar nahi dikh rahi toh "Configure GitHub App" par click karke repository access de dein).

3. **Deploy Blueprint:**
   - Service Name verify karein aur **"Apply"** par click karein.
   - Render automatically:
     - `ai-career-coach-backend` (FastAPI Python service) deploy karega.
     - `ai-career-coach-frontend` (Next.js service) deploy karega.
     - Frontend ko backend ki public URL automatically provide kar dega.

4. **Environment Variables (Optional / AI Keys):**
   - Backend service ke **Environment** tab me jakar aap apni AI API Keys add kar sakte hain:
     - `GROQ_API_KEY`: Aapki Groq key
     - `GEMINI_API_KEY`: Aapki Gemini key

---

## 🛠 Option 2: Manual Web Service Setup on Render

Agar aap manually dono services create karna chahte hain:

### 1. Backend Service (FastAPI):
- **New +** -> **Web Service**
- Repository: `tushar-kumar-code/ai-career-coach`
- **Name:** `ai-career-coach-backend`
- **Root Directory:** `backend`
- **Runtime:** `Python 3`
- **Build Command:** `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Plan:** `Free`
- **Environment Variables:**
  - `PROJECT_NAME`: `AI Career Coach API`
  - `API_V1_STR`: `/api/v1`
  - `DEBUG`: `false`
  - `ENVIRONMENT`: `production`
  - `PYTHON_VERSION`: `3.11.9`
  - `SECRET_KEY`: `generate-any-secure-64-character-secret-key`
  - `BACKEND_CORS_ORIGINS`: `*`
  - `AI_PROVIDER`: `groq`
  - `GROQ_API_KEY`: `your_groq_key_here`
  - `GEMINI_API_KEY`: `your_gemini_key_here`

---

### 2. Frontend Service (Next.js):
- **New +** -> **Web Service**
- Repository: `tushar-kumar-code/ai-career-coach`
- **Name:** `ai-career-coach-frontend`
- **Root Directory:** `frontend`
- **Runtime:** `Node`
- **Build Command:** `npm install && npm run build`
- **Start Command:** `npm run start`
- **Plan:** `Free`
- **Environment Variables:**
  - `NODE_VERSION`: `20`
  - `NEXT_PUBLIC_API_URL`: `https://ai-career-coach-backend.onrender.com` *(Aapke backend service ki Render URL)*

---

## 🎯 Verification Checklist

Deploy hone ke baad:
1. Backend check karein: `https://<your-backend-name>.onrender.com/api/v1/health`
   - Response: `{"status":"healthy","database":"connected",...}`
2. Frontend visit karein: `https://<your-frontend-name>.onrender.com`
   - Login / Assessment / Resume / Practice saare features seamlessly live chalenge.
