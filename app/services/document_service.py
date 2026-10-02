import os
import uuid
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.document import Document
from app.utils.file_processing import ensure_storage_dir, save_upload_file, extract_text
from app.core.config import settings

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'md', 'png', 'jpg', 'jpeg', 'webp'}

class DocumentService:
    def __init__(self):
        ensure_storage_dir()

    def _get_extension(self, filename: str) -> str:
        if '.' not in filename:
            return ""
        return filename.rsplit('.', 1)[1].lower()

    async def upload_document(self, file: UploadFile, db: AsyncSession) -> Document:
        ext = self._get_extension(file.filename)
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File extension {ext} not allowed.")

        # Generate unique filename for storage
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        storage_path = os.path.join(settings.STORAGE_PATH, safe_filename)

        # Save physical file
        await save_upload_file(file, storage_path)

        # For Phase 4, just test extraction to ensure it works, but we won't chunk/embed until Phase 5
        # extract_text(storage_path, ext)

        # Save to DB
        document = Document(
            id=file_id,
            filename=file.filename,
            file_type=ext,
            storage_path=storage_path
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        return document

    async def get_documents(self, db: AsyncSession):
        result = await db.execute(select(Document).order_by(Document.created_at.desc()))
        return result.scalars().all()

    async def get_document(self, document_id: str, db: AsyncSession):
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalars().first()

    async def delete_document(self, document_id: str, db: AsyncSession):
        doc = await self.get_document(document_id, db)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file
        if os.path.exists(doc.storage_path):
            os.remove(doc.storage_path)
            
        await db.delete(doc)
        await db.commit()

document_service = DocumentService()
