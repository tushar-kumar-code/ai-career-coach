# AI Career Coach — How to Run the Project locally

This document provides simple, step-by-step instructions for running the **AI Career Coach** application (FastAPI Backend + Next.js Frontend) on your Windows machine, as well as pushing code to GitHub.

---

## 📌 Quick Summary of URLs

| Service                                     | Local Address                                                             |
| :------------------------------------------ | :------------------------------------------------------------------------ |
| **Frontend Web App**                  | [http://localhost:3000](http://localhost:3000)                             |
| **Backend API Base**                  | [http://127.0.0.1:8000/api/v1](http://127.0.0.1:8000/api/v1)               |
| **Interactive API Docs (Swagger UI)** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)                   |
| **Backend Health Check**              | [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health) |

---

## 🚀 How to Run the Project (Step-by-Step)

To run the complete application, open **two terminal windows** (PowerShell or Command Prompt).

---

### Step 1: Start the Backend Server (Terminal 1)

Open your first terminal window and execute:

```powershell
# 1. Navigate to the backend directory
cd c:\Users\user\tushar\ai-career-coach\backend

# 2. Activate the Python virtual environment
.\venv\Scripts\activate

# 3. Start the FastAPI backend server
python -m uvicorn app.main:app --port 8000 --reload
```

> **Expected Output:**
> You should see:
> `INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`
> `INFO: Application startup complete.`

---

### Step 2: Start the Frontend Application (Terminal 2)

Open a **second terminal window** and execute:

```powershell
# 1. Navigate to the frontend directory
cd c:\Users\user\tushar\ai-career-coach\frontend

# 2. Start the Next.js development server
npm run dev
```

> **Expected Output:**
> You should see:
> `- Local: http://localhost:3000`
> `- Ready in X.Xs`

---

### Step 3: Open the Web Application

Once both servers are running:

1. Open your browser and go to: **[http://localhost:3000](http://localhost:3000)**
2. Access the features:
   - **Dashboard:** `http://localhost:3000/dashboard`
   - **Career Discovery Assessment:** `http://localhost:3000/assessment`
   - **Resume Intelligence System:** `http://localhost:3000/resume`
   - **Skill Intelligence System:** `http://localhost:3000/skills`
   - **Career Digital Twin Profile:** `http://localhost:3000/profile`

---

## ⚡ Option: Launch Both Servers Simultaneously (Single PowerShell Command)

If you prefer to start both backend and frontend automatically with a single command, open PowerShell in the project root (`c:\Users\user\tushar\ai-career-coach`) and run:

```powershell
Start-Process powershell -ArgumentList "-NoExit -Command cd c:\Users\user\tushar\ai-career-coach\backend; .\venv\Scripts\activate; python -m uvicorn app.main:app --port 8000 --reload"; Start-Process powershell -ArgumentList "-NoExit -Command cd c:\Users\user\tushar\ai-career-coach\frontend; npm run dev"
```

This will automatically launch two separate terminal windows—one for backend and one for frontend!

---

## 🐙 GitHub Push Guide (Terminal Ke Through Code Push Kaise Karein)

Aapka remote repository already configured hai:
`https://github.com/tushar-kumar-code/ai-career-coach.git` (Branch: `main`)

### ⚡ Abhi Current Changes Push Karne Ke Liye:

Aapke saare changes locally commit ho chuke hain! Bas terminal (PowerShell) open karein aur ye run karein:

```powershell
cd c:\Users\user\tushar\ai-career-coach
git push origin main
```

---

### 📝 Har Baar Naye Changes Push Karne Ka Complete Process:

Jab bhi aap code me koi change karein ya naya feature add karein, terminal me ye 4 steps follow karein:

#### 1. Status Check Karein:
```powershell
cd c:\Users\user\tushar\ai-career-coach
git status
```
*(Isse aapko pata chalega kaun kaun si files modify ya create hui hain)*

#### 2. Saare Changes Stage Karein:
```powershell
git add .
```

#### 3. Commit Message Likhein:
```powershell
git commit -m "Aapka commit message yaha likhein"
```

#### 4. GitHub Par Push Karein:
```powershell
git push origin main
```

---

### 🔐 Agar GitHub Authentication / Password Maange:

Jab aap pehli baar `git push origin main` karte hain, toh Git aapse login maang sakta hai:

1. **Option 1 (Browser Login - Sabse Aasan):**
   - Agar browser window popup hoti hai, toh **"Sign in with your browser"** par click karein aur GitHub account authorize kar dein.
2. **Option 2 (Personal Access Token - PAT):**
   - Agar password maange, toh apna regular GitHub account password mat daaliye (GitHub security reasons se direct password allow nahi karta).
   - Apne GitHub account me jayein:
     - **GitHub.com** → **Settings** (top-right avatar) → **Developer settings** (bottom-left) → **Personal access tokens** → **Tokens (classic)**
     - Click **Generate new token (classic)**
     - Name de dijiye (e.g., `career-coach-token`), Expiration choose karein, aur **`repo`** checkbox par tick karein.
     - Token generate hone ke baad use copy karein.
   - Terminal me jab `Password for 'https://...':` puche, toh wahi Token paste kar dein (paste karte waqt characters dikhai nahi denge, bus paste karke Enter daba dein).

---

## 🛠️ Database Setup & Database Migrations (If Needed)

The project uses SQLite located at `backend/aicareercoach.db`.

If you ever add new database models or need to re-apply migrations:

```powershell
cd c:\Users\user\tushar\ai-career-coach\backend
.\venv\Scripts\activate

# Apply all database migrations
python -m alembic upgrade head
```

---

## 🧪 Running Automated Tests & Type Checks

### Run Backend Pytest Suite:

```powershell
cd c:\Users\user\tushar\ai-career-coach\backend
.\venv\Scripts\activate
python -m pytest
```

### Run Frontend TypeScript Check:

```powershell
cd c:\Users\user\tushar\ai-career-coach\frontend
npx tsc --noEmit
```

---

## ⚙️ Environment Files Reference

### Backend Environment File: `backend/.env`

```env
PROJECT_NAME="AI Career Coach"
API_V1_STR="/api/v1"
SECRET_KEY="your-super-secret-key-change-in-production"
ENVIRONMENT="development"

# Database Configuration (SQLite)
DATABASE_URL="sqlite+aiosqlite:///./aicareercoach.db"

# Gemini AI Configuration
GEMINI_API_KEY=""
```

### Frontend Environment File: `frontend/.env.local`

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
```

---

## 🛑 How to Stop the Project

To stop the running servers, simply click on each terminal window and press **`Ctrl + C`**.
