import pytest
from fastapi.testclient import TestClient
from app.main import app
import pymupdf

client = TestClient(app)

def test_resume_rejection_sorry_message():
    # 1. Create a dummy text PDF that is NOT a resume (e.g. an invoice / receipt)
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), """
    TAX INVOICE / BILL TO:
    Invoice Number: INV-9921
    GSTIN: 07AAAAA0000A1Z5
    Total Amount Due: $450.00
    Terms and conditions: Payment due upon receipt.
    """)
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("invoice.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/v1/resume/upload", files=files)
    assert response.status_code == 400
    assert "Sorry hum aapke baare me nahi jaan payen hai toh please assesment dijiye." in response.json()["detail"]

def test_resume_short_text_sorry_message():
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hi")
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("short.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/v1/resume/upload", files=files)
    assert response.status_code == 400
    assert "Sorry hum aapke baare me nahi jaan payen hai toh please assesment dijiye." in response.json()["detail"]
