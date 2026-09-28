import re
import io
import uuid
import pymupdf
import docx
from typing import Tuple
from fastapi import UploadFile, HTTPException
from app.services.firestore.client import FirestoreClient

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class DocumentExtractor:
    """Service for validating, processing in-memory, and storing resumes in Firebase Storage."""

    async def process_uploaded_file(self, file: UploadFile, user_id: str) -> Tuple[str, str, str]:
        """
        Validates file, processes PDF/DOCX entirely in memory,
        and uploads to Firebase Storage at users/{user_id}/resumes/{unique_filename}.
        Returns: (storage_path, filename, raw_text)
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is empty")

        filename = re.sub(r"[/\\]", "_", file.filename.strip())
        ext = re.search(r"(\.[a-zA-Z0-9]+)$", filename)
        ext_str = ext.group(1).lower() if ext else ""

        if ext_str not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext_str}'. Only PDF (.pdf) and Word (.docx) files are supported."
            )

        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes)")

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 10MB")

        # 1. In-memory text extraction without writing to local disk
        raw_text = ""
        try:
            if ext_str == ".pdf":
                raw_text = self._extract_text_from_pdf_bytes(content)
            elif ext_str == ".docx":
                raw_text = self._extract_text_from_docx_bytes(content)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read document contents. File may be corrupted or password-protected. Error: {str(e)}"
            )

        raw_text_clean = raw_text.strip()
        if len(raw_text_clean) < 20:
            raise HTTPException(
                status_code=400,
                detail="Extracted text is too short or empty. Please upload a document containing readable text."
            )

        # 2. Upload directly to Firebase Storage under users/{user_id}/resumes/{unique_filename}
        clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
        unique_filename = f"{uuid.uuid4().hex[:8]}_{clean_name}"
        storage_path = f"users/{user_id}/resumes/{unique_filename}"

        content_type = file.content_type or ("application/pdf" if ext_str == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        storage_uri = await FirestoreClient.upload_file(storage_path, content, content_type=content_type)

        return storage_uri, filename, raw_text_clean

    def _extract_text_from_pdf_bytes(self, content: bytes) -> str:
        text_content = []
        doc = pymupdf.open(stream=content, filetype="pdf")
        for page in doc:
            text_content.append(page.get_text())
        doc.close()
        return "\n".join(text_content)

    def _extract_text_from_docx_bytes(self, content: bytes) -> str:
        doc = docx.Document(io.BytesIO(content))
        text_content = [p.text for p in doc.paragraphs if p.text]
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
                if row_text:
                    text_content.append(row_text)
        return "\n".join(text_content)
