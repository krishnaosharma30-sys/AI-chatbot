from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.chat_service import chat_service
from app.db.database import get_db
import uuid

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    attachments: list[str] = []
    use_web_search: bool = False

class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    sources: list = []
    used_rag: bool = False
    used_web_search: bool = False
    new_documents: list = []

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    conv_id = request.conversation_id or str(uuid.uuid4())
    
    # Get response from AI provider, passing DB session and attachments
    response_dict = await chat_service.get_chat_response(
        request.message, conv_id, db, attachments=request.attachments, use_web_search=request.use_web_search
    )
    
    response = ChatResponse(
        answer=response_dict["answer"],
        conversation_id=conv_id,
        sources=response_dict["sources"],
        used_rag=response_dict["used_rag"],
        used_web_search=response_dict.get("used_web", False),
        new_documents=response_dict.get("new_documents", [])
    )
    return response
