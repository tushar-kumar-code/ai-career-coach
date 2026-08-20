import os
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
import pymupdf

client = TestClient(app)


def test_resume_upload_and_analysis_pdf():
    # 1. Create a dummy text PDF in memory using pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), """
Jane Doe
Email: jane.doe@example.com
Phone: (555) 123-4567
LinkedIn: linkedin.com/in/janedoe

Professional Summary:
Experienced Full Stack Developer with 4 years of experience building Python and React applications.

Work Experience:
Senior Software Engineer - TechCorp Systems
- Built scalable FastAPI microservices handling 50,000 requests per minute with Redis caching.
- Developed responsive React and TypeScript frontend UI components.

Technical Skills:
Python, JavaScript, TypeScript, React, FastAPI, PostgreSQL, Docker, Git
""")
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Upload PDF
    files = {"file": ("test_resume.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/v1/resume/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["ats_score"] >= 60
    assert data["data"]["contact_info"]["email"] == "jane.doe@example.com"
    assert "Python" in [s["name"] for s in data["data"]["extracted_skills"]]


def test_resume_unsupported_file_format():
    files = {"file": ("test.txt", b"Plain text file content", "text/plain")}
    response = client.post("/api/v1/resume/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_resume_empty_file():
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    response = client.post("/api/v1/resume/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_get_resume_analysis_and_skills():
    # 1. Get Analysis
    response = client.get("/api/v1/resume/analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is not None
    assert "ats_breakdown" in data["data"]

    # 2. Get Skills
    skills_resp = client.get("/api/v1/resume/skills")
    assert skills_resp.status_code == 200
    skills_data = skills_resp.json()
    assert skills_data["success"] is True
    assert len(skills_data["data"]) >= 1
