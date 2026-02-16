from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes

from src.app.rag.chain import build_chain

DEFAULT_PORT = 8000

def ensure_vectorstore() -> None:
    storage_dir = Path(os.getenv("VECTORSTORE_DIR", "storage"))
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    marker = storage_dir / "manifest.json"
    if marker.exists():
        return
    
    from src.app.ingest.loader import DEFAULT_SEEDS, load_urls
    from src.app.ingest.indexer import index_documents

    docs = load_urls(DEFAULT_SEEDS)
    index_documents(
        docs=docs,
        seeds=DEFAULT_SEEDS,
        storage_dir=storage_dir,
    )


def create_app() -> FastAPI:
    app = FastAPI(title="Promtior RAG API", version="1.0.0")

    allow_origins = [
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:3000",
        "HTTP://127.0.0.1:3000",
        "*",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/health")
    def health():
        return {"status": "ok"}    

    ensure_vectorstore()
    chain = build_chain()

    add_routes(
        app,
        chain,
        path="/chat",
        playground_type="default",
    )
    
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", str(DEFAULT_PORT)))
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=port, reload=False)