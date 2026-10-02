from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import chat, health, conversations, documents, audio
from app.db.database import engine, Base
import app.models  # Ensure all SQLAlchemy models are registered

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically initialize database schema on startup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database schema initialized successfully.")
    except Exception as e:
        print(f"Database initialization warning: {e}")
    yield

app = FastAPI(
    title="Multimodal AI Chatbot API",
    description="API for the Multimodal AI Chatbot MVP",
    version="1.0.0",
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS] if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])

@app.get("/")
def root():
    return {"message": "Welcome to the Multimodal AI Chatbot API. Visit /docs for documentation."}
