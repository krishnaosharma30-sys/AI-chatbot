import os
import shutil
from fastapi import UploadFile, HTTPException
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from app.core.config import settings

def ensure_storage_dir():
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)

async def save_upload_file(upload_file: UploadFile, destination_path: str):
    try:
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()

def extract_text(file_path: str, file_type: str) -> str:
    """Extracts text based on file type."""
    try:
        if file_type == 'pdf':
            return extract_text_from_pdf(file_path)
        elif file_type == 'docx':
            return extract_text_from_docx(file_path)
        elif file_type in ['txt', 'md']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text from {file_type}: {str(e)}")

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, 'rb') as f:
        reader = PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file_path: str) -> str:
    doc = DocxDocument(file_path)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])
