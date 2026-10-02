# Multimodal AI Assistant

A beginner-friendly but fully-featured Multimodal AI Chatbot MVP built with FastAPI (Python), React, and PostgreSQL. 

This project demonstrates a robust, extensible architecture without unnecessary enterprise complexity (no microservices, no mandatory auth). It is perfect for a college project, hackathon prototype, or portfolio showcase.

## Features ✨

- **Text Chat:** Conversational memory backed by PostgreSQL.
- **RAG (Retrieval-Augmented Generation):** Upload PDF, DOCX, TXT, or MD documents. The system chunks and embeds them using Google Gemini embeddings and stores them in PostgreSQL using `pgvector` for semantic search.
- **Image Understanding:** Attach images (PNG, JPG, WEBP) directly to the chat. The AI will analyze and discuss them natively.
- **Voice / Audio:** 
  - **STT (Speech-to-Text):** Click the 🎤 button to record your voice using the browser, transcribed via OpenAI Whisper.
  - **TTS (Text-to-Speech):** Click the 🔊 button on the AI's responses to hear them spoken aloud via OpenAI TTS.
- **Agentic Web Search:** Toggle the 🌐 button to allow the AI to search the web (via DuckDuckGo) for real-time information to answer your query.
- **Document Creation:** Ask the AI to write an essay or save a note. It will automatically intercept the output and save it as a Markdown file in your workspace, adding it to your Document Tray.
- **Emotional Intelligence:** System prompts are configured to respond empathetically and supportively to emotional inputs.

---

## Architecture 🏗️

- **Frontend:** React + Vite, modern CSS styling (Dark mode, glassmorphism, flexbox layout). Uses `react-markdown` for rich text rendering.
- **Backend:** FastAPI, strictly modularized by routes, schemas, models, and services.
- **Database:** PostgreSQL with `pgvector` extension for vector similarity search. Interfaced using SQLAlchemy async engine.
- **AI Providers:** 
  - Google Gemini (`gemini-2.5-flash`) for text, reasoning, and image understanding.
  - Google Gemini (`text-embedding-004`) for document chunk embeddings.
  - OpenAI for STT and TTS.

---

## Setup Instructions 🚀

### Prerequisites
1. **Docker Desktop** (for PostgreSQL database).
2. **Python 3.10+**
3. **Node.js 18+**

### 1. Database Setup
Start the PostgreSQL database with the pgvector extension using Docker Compose:
```bash
docker-compose up -d
```

### 2. Backend Setup
Navigate to the `backend` directory and set up your virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

Install requirements:
```bash
pip install -r requirements.txt
```

Run database migrations to create the tables (this requires the `docker-compose` DB to be running):
```bash
alembic upgrade head
```

Start the backend server:
```bash
uvicorn app.main:app --reload
```

### 3. Frontend Setup
Open a new terminal and navigate to the `frontend` directory:

```bash
npm install
npm run dev
```

### 4. Environment Variables
Create a `.env` file in the root directory (you can copy `.env.example`). You must provide:
- `AI_API_KEY`: Your Google Gemini API Key.
- `OPENAI_API_KEY`: Your OpenAI API key (required for voice features).

---

## How to Use 💡

1. **Start a Chat:** Just type a message and hit Send.
2. **Upload Documents:** Click the 📎 icon to attach text/PDF files. Wait a few seconds for the backend to chunk and embed them. Then ask questions about them.
3. **Analyze Images:** Click the 📎 icon to attach an image. Ask "What is in this image?"
4. **Voice Input:** Click the 🎤 icon, grant microphone permissions, speak, and click it again to stop.
5. **Web Search:** Click the 🌐 icon to toggle web search on before sending your message.
6. **Create a Document:** Ask "Write a short poem and save it as poem.md". The file will automatically save and appear in your active Document Tray.

## Project Structure 📁

```text
Chatbot/
├── .env                  # Environment keys
├── docker-compose.yml    # PGVector DB
├── requirements.txt      # Python dependencies
├── backend/
│   ├── alembic/          # DB Migrations
│   ├── app/
│   │   ├── api/routes/   # FastAPI Endpoints
│   │   ├── core/         # Config
│   │   ├── db/           # SQLAlchemy Engine
│   │   ├── models/       # DB Entities (SQLAlchemy)
│   │   ├── schemas/      # Pydantic Validation
│   │   ├── services/     # Business Logic (AI, RAG, Audio, Chat)
│   │   ├── utils/        # Chunking, File parsing
│   │   └── main.py       # App Entrypoint
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── App.jsx       # Main UI Component
│   │   └── App.css       # UI Styling
│   └── package.json
```
