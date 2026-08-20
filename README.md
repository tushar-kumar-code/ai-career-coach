# AI Career Coach

AI Career Coach is an intelligent career guidance web application featuring:
1. **Career Discovery System:** 12-dimension adaptive evaluation and career archetype matching.
2. **Resume Intelligence System:** PDF/DOCX text extraction, algorithmic ATS sub-scores, target career skill matching, and AI bullet rewrites.
3. **Skill Intelligence System:** Normalized multi-source evidence tracking, system confidence levels (*Claimed*, *Supported*, *Verified*), and target career gap priority calculations.
4. **Career Digital Twin:** Real-time synchronized profile.

---

## 🚀 How to Run the Project

For complete instructions on running the project in terminal, see **[RUN_PROJECT.md](RUN_PROJECT.md)**.

### Quick Start:

1. **Terminal 1 (Backend - FastAPI):**
   ```powershell
   cd backend
   .\venv\Scripts\activate
   python -m uvicorn app.main:app --port 8000 --reload
   ```

2. **Terminal 2 (Frontend - Next.js):**
   ```powershell
   cd frontend
   npm run dev
   ```

3. Open **[http://localhost:3000](http://localhost:3000)** in your browser.
