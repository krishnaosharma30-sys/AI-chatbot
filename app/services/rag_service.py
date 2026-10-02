import math
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.utils.file_processing import extract_text
from app.utils.chunking import chunk_text
from app.services.embedding_service import get_embedding_provider
from app.core.config import settings

def cosine_similarity(v1, v2) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

class RAGService:
    def __init__(self):
        self.embedding_provider = get_embedding_provider(settings.AI_API_KEY)

    async def process_document(self, document_id: str, db: AsyncSession):
        """Extracts text, chunks it, generates embeddings, and saves to DB."""
        # Get document
        doc = await db.execute(select(Document).where(Document.id == document_id))
        doc = doc.scalars().first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if already processed (chunks exist)
        existing = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id).limit(1))
        if existing.scalars().first():
            return {"status": "already_processed"}

        # Extract text
        text = extract_text(doc.storage_path, doc.file_type)
        if not text.strip():
            return {"status": "no_text_found"}

        # Chunk text
        chunks = chunk_text(text)
        
        # Embed chunks (batch process for efficiency)
        embeddings = await self.embedding_provider.get_embeddings(chunks)
        
        # Save chunks
        for idx, (chunk_text_content, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunk = DocumentChunk(
                document_id=doc.id,
                content=chunk_text_content,
                embedding=embedding,
                chunk_index=idx,
                metadata_json={"filename": doc.filename}
            )
            db.add(db_chunk)
            
        await db.commit()
        return {"status": "processed", "chunks_created": len(chunks)}

    async def search(self, query: str, db: AsyncSession, top_k: int = 3):
        """Searches for relevant chunks using vector similarity."""
        query_embedding = await self.embedding_provider.get_embedding(query)
        
        # Check dialect if running PostgreSQL with pgvector
        try:
            bind = db.bind
            dialect_name = bind.dialect.name if bind else "sqlite"
        except Exception:
            dialect_name = "sqlite"
        
        if dialect_name == "postgresql":
            try:
                from sqlalchemy import text
                vector_str = f"[{','.join(map(str, query_embedding))}]"
                sql = text("""
                    SELECT dc.id, dc.content, dc.metadata_json, d.filename, (dc.embedding <-> :vector) as distance
                    FROM document_chunks dc
                    JOIN documents d ON dc.document_id = d.id
                    ORDER BY dc.embedding <-> :vector
                    LIMIT :top_k
                """)
                result = await db.execute(sql, {"vector": vector_str, "top_k": top_k})
                rows = result.fetchall()
                results = []
                for row in rows:
                    results.append({
                        "chunk_id": row.id,
                        "content": row.content,
                        "metadata": row.metadata_json,
                        "filename": row.filename,
                        "distance": row.distance
                    })
                return results
            except Exception as e:
                print(f"PostgreSQL pgvector query failed, falling back to python similarity: {e}")

        # Universal fallback (works seamlessly on SQLite and PostgreSQL)
        result = await db.execute(
            select(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
        )
        rows = result.all()
        
        scored_chunks = []
        for chunk, filename in rows:
            emb = chunk.embedding
            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except Exception:
                    emb = []
            score = cosine_similarity(query_embedding, emb)
            scored_chunks.append({
                "chunk_id": chunk.id,
                "content": chunk.content,
                "metadata": chunk.metadata_json,
                "filename": filename,
                "distance": 1.0 - score
            })
            
        scored_chunks.sort(key=lambda x: x["distance"])
        return scored_chunks[:top_k]

rag_service = RAGService()
