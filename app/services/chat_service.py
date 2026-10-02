from typing import List, Dict, Any
from app.services.ai_provider import get_ai_provider
from app.services.rag_service import rag_service
from app.services.web_search_service import web_search_service
from app.core.config import settings
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
import uuid
import json
import re
import os

SYSTEM_PROMPT = """You are a helpful multimodal AI assistant.
You can understand text, images, audio and documents.
Use retrieved documents when they are relevant.
Use web search when current or external information is required.
Do not fabricate facts, citations or sources.
If available context is insufficient, clearly say so.
For emotional conversations, be highly empathetic, supportive, and validating without presenting yourself as a medical professional.
Follow safety requirements at all times.

DOCUMENT CREATION INSTRUCTIONS:
If the user asks you to "save", "create", or "write" a document (like a note, essay, or markdown file) that they can keep for later, output it using the following format. 
You MUST provide the filename in quotes, and wrap the content in the tags. The system will automatically intercept this and save it to their workspace.

[SAVE_DOCUMENT: "filename.md"]
Write your document content here...
[/SAVE_DOCUMENT]
"""

class ChatService:
    def __init__(self):
        self.ai_provider = get_ai_provider(settings.AI_API_KEY)

    async def get_chat_response(self, message_text: str, conversation_id: str, db: AsyncSession, attachments: List[str] = None, use_web_search: bool = False) -> Dict:
        try:
            if attachments is None:
                attachments = []
                
            # 1. Get or create conversation
            result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
            conversation = result.scalars().first()
            if not conversation:
                title = message_text[:30] + "..." if len(message_text) > 30 else message_text
                conversation = Conversation(id=conversation_id, title=title)
                db.add(conversation)
                await db.commit()
                await db.refresh(conversation)

            # 2. Save user message
            user_message = Message(
                conversation_id=conversation_id,
                role="user",
                content=message_text
            )
            db.add(user_message)
            await db.commit()
            
            # Fetch attachment documents if any
            image_paths = []
            if attachments:
                docs = await db.execute(select(Document).where(Document.id.in_(attachments)))
                attached_docs = docs.scalars().all()
                for d in attached_docs:
                    if d.file_type in ['png', 'jpg', 'jpeg', 'webp']:
                        image_paths.append(d.storage_path)
            
            # 3. Perform RAG Search (only if there is text)
            search_results = []
            if message_text.strip():
                try:
                    search_results = await rag_service.search(message_text, db, top_k=3)
                except Exception as rag_err:
                    print(f"RAG search error (safe fallback): {rag_err}")
            
            # 3.5 Perform Web Search if enabled
            web_results = []
            if use_web_search and message_text.strip():
                try:
                    web_results = await web_search_service.search(message_text, max_results=3)
                except Exception as web_err:
                    print(f"Web search error (safe fallback): {web_err}")
            
            # Build Context string from results
            rag_context = ""
            sources = []
            used_rag = False
            used_web = False
            
            if search_results or web_results:
                if search_results: used_rag = True
                if web_results: used_web = True
                
                rag_context = "\n\n--- CONTEXT PROVIDED TO YOU ---\n"
                
                if search_results:
                    rag_context += "From Uploaded Documents:\n"
                    for res in search_results:
                        rag_context += f"- Source: {res['filename']}\n  Content: {res['content']}\n"
                        sources.append({"type": "document", "name": res['filename']})
                        
                if web_results:
                    rag_context += "\nFrom Web Search:\n"
                    for wres in web_results:
                        rag_context += f"- Source: {wres['title']} ({wres['url']})\n  Content: {wres['content']}\n"
                        sources.append({"type": "web", "name": wres['title'], "url": wres['url']})
                        
                rag_context += "--- END CONTEXT ---\n"
                
                unique_sources = []
                for s in sources:
                    if s not in unique_sources:
                        unique_sources.append(s)
                sources = unique_sources

            # 4. Retrieve chat history
            msg_result = await db.execute(
                select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
            )
            history = msg_result.scalars().all()
            
            messages = [{"role": m.role, "content": m.content} for m in history]
            
            # 5. Append context to the last user message before sending to AI
            if used_rag or used_web:
                messages[-1]["content"] += rag_context
                
            # Append images to the last user message
            if image_paths:
                messages[-1]["images"] = image_paths
            
            # 6. Get response from AI provider
            response_text = await self.ai_provider.generate_response(
                messages=messages,
                system_prompt=SYSTEM_PROMPT
            )
            
            # 6.5 Parse for [SAVE_DOCUMENT: "filename.md"]...[/SAVE_DOCUMENT]
            new_documents = []
            doc_pattern = re.compile(r'\[SAVE_DOCUMENT:\s*"([^"]+)"\](.*?)\[/SAVE_DOCUMENT\]', re.DOTALL)
            
            def replace_doc(match):
                filename = match.group(1).strip()
                content = match.group(2).strip()
                
                # Save physically
                file_id = str(uuid.uuid4())
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'txt'
                safe_filename = f"{file_id}_{filename}"
                storage_path = os.path.join(settings.STORAGE_PATH, safe_filename)
                
                os.makedirs(settings.STORAGE_PATH, exist_ok=True)
                with open(storage_path, "w", encoding="utf-8") as f:
                    f.write(content)
                    
                # Create Document record (needs to be done outside this sync func, but we just gather data here)
                new_documents.append({
                    "id": file_id,
                    "filename": filename,
                    "file_type": ext,
                    "storage_path": storage_path
                })
                
                return f"\n*✅ Automatically saved document: **{filename}***\n"

            # Execute regex replacement
            response_text = doc_pattern.sub(replace_doc, response_text)
            
            # Save new docs to DB
            created_docs = []
            for doc_data in new_documents:
                doc_model = Document(
                    id=doc_data["id"],
                    filename=doc_data["filename"],
                    file_type=doc_data["file_type"],
                    storage_path=doc_data["storage_path"]
                )
                db.add(doc_model)
                created_docs.append({
                    "id": doc_model.id,
                    "filename": doc_model.filename,
                    "file_type": doc_model.file_type,
                    "created_at": None
                })
            
            # 7. Save AI message
            ai_message = Message(
                conversation_id=conversation_id,
                role="ai",
                content=response_text
            )
            db.add(ai_message)
            await db.commit()

            return {
                "answer": response_text,
                "sources": sources,
                "used_rag": used_rag,
                "used_web": used_web,
                "new_documents": created_docs
            }
        except Exception as e:
            await db.rollback()
            print(f"ChatService Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

chat_service = ChatService()
