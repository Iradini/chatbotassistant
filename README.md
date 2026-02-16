# CHATBOT ASSISTANT

Minimal scaffold for a RAG chatbot with LangChain + LangServer

### Requirements

- Python 3.11

#### Create environment (venv)

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version

#### Create environment (conda)

conda create -n protmiorchatbot python=3.11
conda activate promtiorchatbot
python --version

## Install dependencies

python -m pip install -r requirements.txt

## Configuration

copy .env.example .env

## Health check

http://127.0.0.1:8000/health

## Deploy on Railway (3 services)

This project deploys as three services in **one Railway project:**

- **ui** (Streamlit, public)
- **backend** (LangServe/FastAPI, private)
- **ollama** (model server, private)

### Service names (important for internal DNS)

- UI: `ui`
- Backend: `backend`
- Ollama: `ollama`

Railway internal DNS is:

- `http://backend.railway.internal:<PORT>`
- `http://ollama.railway.internal:11434`

### Environment variables

**UI service**

- `LANGSERVE_BASE_URL` = `http://backend.railway.internal:8000`
- `PORT` = provided by Railway

**Backend Service**

- `PORT` = `8000` (set explicitly for stable internal calls)
- `OLLAMA_BASE_URL` = `http://ollama.railway.internal:11434`
- `OLLAMA_LLM_MODEL` = `llama2`
- `OLLAMA_EMBED_MODEL` = `nomic-embed-text`
- `VECTORSTORE_DIR` = `/data/storage`

**Ollama service**

- `OLLAMA_HOST` = `0.0.0.0:11434`
- `OLLAMA_MODELS` = `/data/models`
- `PORT` = `11434`

### Volumes (important)

- **Ollama**: mount a volume to `/data` so models persist.
- **Backend**: mount a volume to `/data` so vectorstore persists.

### Notes

- Backend and Ollama stay private. Only UI is public.
- If you need to rebuild the vectorestore, run the ingestion script in the backend service or during build (no recommended for large sites).
