import re
import io
import uuid
import pymupdf
import docx
from typing import Tuple
from fastapi import UploadFile, HTTPException
from app.services.firestore.client import FirestoreClient

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


class DocumentExtractor:
    """Service for validating, processing in-memory, and extracting text from resumes."""

    async def process_uploaded_file(self, file: UploadFile, user_id: str) -> Tuple[str, str, str]:
        """
        Validates file, processes PDF/DOC/DOCX entirely in memory.
        Returns: (storage_path, filename, raw_text)
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is empty. Please upload only resume.")

        filename = re.sub(r"[/\\]", "_", file.filename.strip())
        ext = re.search(r"(\.[a-zA-Z0-9]+)$", filename)
        ext_str = ext.group(1).lower() if ext else ""

        if ext_str not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext_str}'. Only PDF (.pdf) and Word (.doc, .docx) formats are supported. Please upload only resume. (Kripya keval apna resume hi upload karein)"
            )

        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes). Please upload only resume.")

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 10MB.")

        # 1. In-memory text extraction without writing to local disk or cloud bucket
        raw_text = ""
        try:
            if ext_str == ".pdf":
                raw_text = self._extract_text_from_pdf_bytes(content)
            elif ext_str == ".docx":
                raw_text = self._extract_text_from_docx_bytes(content)
            elif ext_str == ".doc":
                raw_text = self._extract_text_from_doc_bytes(content)
        except Exception as e:
            del content
            import gc
            gc.collect()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read document contents. File may be corrupted or password-protected. Error: {str(e)}"
            )

        # 2. Immediately wipe the binary file bytes from RAM
        del content
        import gc
        gc.collect()

        raw_text_clean = raw_text.strip()
        if len(raw_text_clean) < 30:
            raise HTTPException(
                status_code=400,
                detail="Sorry hum aapke baare me nahi jaan payen hai toh please assesment dijiye."
            )

        # Transient in-memory extraction
        storage_uri = None

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
        text_content = []
        # Iterate over body elements in exact document order so tables appear under their headings
        for element in doc.element.body:
            if element.tag.endswith('p'):
                p = docx.text.paragraph.Paragraph(element, doc)
                if p.text and p.text.strip():
                    text_content.append(p.text.strip())
            elif element.tag.endswith('tbl'):
                t = docx.table.Table(element, doc)
                for row in t.rows:
                    seen_cells = set()
                    cell_texts = []
                    for cell in row.cells:
                        c_text = cell.text.strip()
                        if c_text and id(cell._tc) not in seen_cells:
                            seen_cells.add(id(cell._tc))
                            cell_texts.append(c_text)
                    if cell_texts:
                        text_content.append(" | ".join(cell_texts))
        return "\n".join(text_content)

    def _extract_text_from_doc_bytes(self, content: bytes) -> str:
        """Extracts text from Word 97-2004 (.doc) or renamed docx in memory."""
        # 1. Try docx parser first in case it is an OpenXML file with .doc extension
        try:
            extracted = self._extract_text_from_docx_bytes(content)
            if len(extracted.strip()) > 30:
                return extracted
        except Exception:
            pass

        # 2. Extract printable ASCII sequences
        extracted_lines = []
        ascii_strings = re.findall(b"[\x20-\x7E\t\r\n]{4,}", content)
        for s in ascii_strings:
            try:
                decoded = s.decode("ascii", errors="ignore").strip()
                if len(decoded) > 3 and not all(c in "_\-=*#\x00" for c in decoded):
                    extracted_lines.append(decoded)
            except Exception:
                continue

        # 3. Extract UTF-16LE 2-byte sequences (common in Word CFBF streams)
        utf16_matches = re.findall(b"(?:[\x20-\x7E][\x00]){4,}", content)
        for s in utf16_matches:
            try:
                decoded = s.decode("utf-16le", errors="ignore").strip()
                if len(decoded) > 3 and not all(c in "_\-=*#" for c in decoded):
                    extracted_lines.append(decoded)
            except Exception:
                continue

        combined = "\n".join(extracted_lines)
        if len(combined.strip()) > 30:
            return combined

        raise ValueError("Could not extract readable text from .doc file. Please save as .docx or .pdf and upload again.")
