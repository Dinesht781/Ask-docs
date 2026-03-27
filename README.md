# Ask-Docs

Ask-Docs is a simple Retrieval Augmented Generation (RAG) chatbot application built with:
- FastAPI backend (`api/`)
- Streamlit frontend (`app/`)
- ChromaDB for vector indexing (`api/chroma_db`)
- LangChain + OpenAI models for semantic retrieval and answer generation
- SQLite for application logs and document metadata

## Features

- Upload PDF / DOCX / HTML documents
- Convert documents to vector embeddings and store in ChromaDB
- RAG chat interface with session context and history
- WebSocket real-time interaction + REST API support
- Document list, delete, and metadata management

## Project structure

- `main.py` - script entrypoint (prints welcome message)
- `api/` - backend service, data models, vectorization and database utilities
  - `api/main.py` - FastAPI app with endpoints for `/chat`, `/upload-doc`, `/list-docs`, `/delete-doc`, and `/ws`
  - `api/pydantic_models.py` - request/response schema definitions
  - `api/chroma_utils.py` - document loader/splitter/indexer functions
  - `api/langchain_utils.py` - RAG chain creation and model prompt logic
  - `api/db_utils.py` - SQLite helpers and chat history logging
  - `api/test.py` - WebSocket test client
- `app/` - Streamlit UI
  - `app/streamlit_app.py` - app entry with UI composition
  - `app/sidebar.py` - document manager & model picker UI
  - `app/chat_interface.py` - chat interface and message loop
  - `app/api_utils.py` - HTTP/WebSocket client helpers

## Prerequisites

- Python 3.11 (suggested)
- `pip` package manager
- GOOGLE API key set as environment variable:
  - `GOOGLE_API_KEY` (for `langchain_google_genai` usage)

## Install dependencies

```bash
cd c:/projects/Ask-docs
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

## Setup database (done automatically on first run)

- `api/db_utils.py` creates two tables:
  - `application_logs`
  - `document_store`

## Run backend

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:
- POST `/chat` with JSON `{"question":"...", "model":"gemini-2.5-flash", "session_id":"..."}`
- POST `/upload-doc` with form data file field `file`
- GET `/list-docs`
- POST `/delete-doc` with JSON `{"file_id": <id>}`
- WS `/ws` for interactive chat

## Run frontend

```bash
streamlit run app/streamlit_app.py
```

Then open the local Streamlit URL (<http://localhost:8501> by default).

## Usage

1. Choose model in sidebar (gemini-2.5-flash or gemini-2.0-flash).
2. Upload a supported document.
3. Ask questions in the chat box.
4. View chatbot response and then continue conversation.
5. Use "Refresh Document List" and "Delete Selected Document" as needed.

## Troubleshooting

- Ensure the backend is running before launching Streamlit.
- Confirm `GOOGLE_API_KEY` is set in environment or `.env`.
- If deployment fails with vector store errors, clear `chroma_db/` and restart.

## Notes

- Persistence for embeddings is configured in `api/chroma_utils.py`.
- Session history is held in SQLite and used by `langchain_utils.get_rag_chain()` for context-aware prompts.
- Docstrings are now added across modules for maintainability and readability.
