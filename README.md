# Promtior RAG Chatbot Assistant

RAG-based chatbot with built with:

- LangChain
- LangServe (FastAPI)
- Streamlit (UI)
- Ollama (LLM + embeddings)
- Docker Compose

The assistant answer questions about Promtior using website content and a presentation PDFas knowledge source

---

# Architecture Overview

User
↓
Streamlit UI
↓
LangServe (FastAPI backend)
↓
Retriever
↓
Vectorstore
↓
Ollama (llama2 + nomic-embed-text)
↓
Response + Sources

### Services (Docker Compose):

- `ui` (Streamlit) → exposed on **http://localhost:8501**
- `backend` (FastAPI) → exposed on **http://localhost:8000**
- `ollama` → exposed on **http://localhost:11434**

Data persistence:

- Vector store and manifests are stored in a Docker volume.

---

# Requirements

- Docker + Docker Compose plugin
- Enough resources to run Ollama models (8GB RAM minimum; 16GB recomended for production)

---

# Quickstart (Docker Compose)

This is the recommended way to run the project locally.

## 1) Start services

```
bash

docker compose up -d --build
docker compose ps
```

### 2) Pull models (first time only)

```
bash

OLLAMA_CID=$(docker ps -qf "name=ollama")

docker exec -it $OLLAMA_CID ollama pull llama2
docker exec -it $OLLAMA_CID ollama pull nomic-embed-text
```

### 3) Restart backend (if needed)

```
bash

docker compose restart backend
```

### 4) Open UI

- http://localhost:8501

### 5) Health check

- http://127.0.0.1:8000/health

---

## Rebuilding the Vectorstore

If you modify sources (website or presentation), re-run the ingestion process inside the backend container.

```
bash

docker compose exec backend python scripts/ingest.py
```

---

### Notes on sources

The knowledge base is built from:

- Promtior website pages (web ingestion)
- Presentation PDF (ingested as `presentation:<filename>#page=<n>` sources)

The assistant answers **only** using retrieved context; if information is not present in the indexed sources, it returns the fallback message.

---

## Deployment (Planned / Improvement)

Due to time constraints of the technical assessment timeframe, the cloud deployment (AWS/Railway) is not included in the final delivery.
The application is fully containerized and reproducible via Docker Compose (see Quickstart above), and the deployment work is planned as an immediate next step.

### Planned deployment approach

- Deploy UI (Streamlit) + Backend (LangServe) + Ollama on a cloud VM (e.g., AWS EC2) using Docker Compose.
- Expose only the UI port publicly; keep Ollama private.
- Persist models and vector store via volumes.

This approach requires sufficient disk and memory for Ollama models and is operationally straightforward given the existing containerization.

---

## Improvements / Next Steps

1) **Cloud deployment**

   - AWS EC2 deployment with Docker Compose (UI + Backend + Ollama) and security hardening (only UI port public).
   - Optional: domain + HTTPS termination.
2) **Automated tests**

   - Unit tests for ingestion utilities (loader, chunking, metadata normalization).
   - Integration tests for LangServe endpoints (e.g., `/health`, `/chat/invoke`) with a lightweight mocked LLM.
   - RAG regression tests with golden questions (services, founded) verifying answer contains expected entities and includes Sources.
3) **Observability**

   - Structured logging (JSON) with request IDs.
   - Metrics (latency, retriever hits, token usage if applicable).
   - Tracing (OpenTelemetry) across UI → backend → retrieval → LLM calls.
4) **RAG quality upgrades**

   - Optional re-ranking (cross-encoder) to improve precision.
   - Query rewriting for recall, and source-type routing (web-first vs PDF-first) for specific intents.
5) **Security**

   - Rate-limiting on the API.
   - CORS policy + input validation.
   - Secret management for environment variables.

---

### Environment variables

### **Backend**

- `PORT` = `8000`
- `OLLAMA_BASE_URL` = `http://ollama:11434`
- `OLLAMA_LLM_MODEL` = `llama2`
- `OLLAMA_EMBED_MODEL` = `nomic-embed-text`
- `VECTORSTORE_DIR` = `/data/storage`

### **UI**

- `PORT` = `8000`
- `LANGSERVE_BASE_URL` = `http://backend:8000`

### **Ollama**

- `OLLAMA_HOST` = `0.0.0.0:11434`
- `OLLAMA_MODELS` = `/data/models`
