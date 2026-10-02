from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_db, AsyncSessionLocal
from app.services.document_service import document_service
from app.services.rag_service import rag_service
from app.schemas.document import DocumentResponse

router = APIRouter()

async def _process_doc_in_background(document_id: str):
    async with AsyncSessionLocal() as session:
        try:
            await rag_service.process_document(document_id, session)
        except Exception as e:
            print(f"Background processing error for document {document_id}: {e}")

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db)
):
    doc = await document_service.upload_document(file, db)
    # Process document in background with fresh session
    background_tasks.add_task(_process_doc_in_background, doc.id)
    return doc

@router.post("/{document_id}/process")
async def process_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await rag_service.process_document(document_id, db)
    return result

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(db: AsyncSession = Depends(get_db)):
    return await document_service.get_documents(db)

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    doc = await document_service.get_document(document_id, db)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    await document_service.delete_document(document_id, db)
    return {"status": "ok", "message": "Document deleted"}
