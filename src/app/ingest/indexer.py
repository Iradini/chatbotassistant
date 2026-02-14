from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Union

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

ENV_BASE_URL = "OLLAMA_BASE_URL"
ENV_EMBED_MODEL = "OLLAMA_EMBED_MODEL"

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_EMBED_MODEL = "nomic-embed-text"

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


@dataclass(frozen=True)
class IndexStats:
    doc_count: int
    chunk_count: int
    storage_dir: Path
    manifest_path: Path


def split_documents(
    docs: Iterable[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(list(docs))


def get_ollama_settings() -> tuple[str, str]:
    base_url = os.getenv(ENV_BASE_URL, DEFAULT_BASE_URL).strip()
    model = os.getenv(ENV_EMBED_MODEL, DEFAULT_EMBED_MODEL).strip()
    if not base_url:
        raise ValueError(
            "OLLAMA_BASE_URL is empty. Define a valid URL, for example http://localhost:11434."
        )
    if not model:
        raise ValueError(
            "OLLAMA_EMBED_MODEL is empty. Define an embedding model, for example nomic-embed-text."
        )
    return base_url, model


def get_embeddings(base_url: str, model: str) -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=model,
        base_url=base_url,
    )


def probe_embeddings(base_url: str, model: str, embeddings: OllamaEmbeddings) -> None:
    try:
        embeddings.embed_query("ping")
    except Exception as exc:  # noqa: BLE001 -
        message = str(exc).lower()
        if "connect" in message or "connection" in message or "refused" in message:
            raise RuntimeError(
                "Could not connect to Ollama. Make sure the server is running "
                f"on {base_url} (for example: `ollama serve`)."
            ) from exc
        if "model" in message and ("not found" in message or "pull" in message):
            raise RuntimeError(
                "The embedding model is not available in Ollama. Download it with "
                f"`ollama pull {model}`."
            ) from exc
        raise RuntimeError(f"Error generating embeddings: {exc}") from exc


def ensure_storage_dir(storage_dir: Union[str, Path]) -> Path:
    storage_path = Path(storage_dir)
    if storage_path.exists() and not storage_path.is_dir():
        raise ValueError(
            f"Storage path exists but is not a directory: {storage_path}"
        )
    if not storage_path.exists():
        try:
            storage_path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OSError(
                f"Could not create storage directory at {storage_path}."
            ) from exc
    return storage_path


def save_manifest(
    storage_dir: Union[str, Path],
    seeds: Iterable[str],
    doc_count: int,
    chunk_count: int,
    chunk_size: int,
    chunk_overlap: int,
    base_url: str,
    embed_model: str,
    vector_store: str,
) -> Path:
    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seeds": list(seeds),
        "doc_count": doc_count,
        "chunk_count": chunk_count,
        "chunking": {
            "splitter": "RecursiveCharacterTextSplitter",
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        },
        "embeddings": {
            "provider": "ollama",
            "model": embed_model,
            "base_url": base_url,
        },
        "vector_store": {
            "type": vector_store,
            "path": str(storage_path.resolve()),
        },
    }

    manifest_path = storage_path / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest_path


def index_documents(
    docs: Iterable[Document],
    seeds: Optional[Iterable[str]] = None,
    storage_dir: Union[str, Path] = "storage",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> IndexStats:
    docs_list = list(docs)
    if not docs_list:
        raise ValueError("No documents were received for indexing.")

    chunks = split_documents(
        docs_list,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    if not chunks:
        raise ValueError("The chunking process produced no results. Check the content of the documents.")

    storage_path = ensure_storage_dir(storage_dir)

    base_url, embed_model = get_ollama_settings()
    embeddings = get_embeddings(base_url=base_url, model=embed_model)
    probe_embeddings(base_url=base_url, model=embed_model, embeddings=embeddings)

    vector_index = FAISS.from_documents(chunks, embeddings)
    vector_index.save_local(str(storage_path))

    manifest_path = save_manifest(
        storage_dir=storage_path,
        seeds=seeds or [],
        doc_count=len(docs_list),
        chunk_count=len(chunks),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        base_url=base_url,
        embed_model=embed_model,
        vector_store="faiss",
    )

    return IndexStats(
        doc_count=len(docs_list),
        chunk_count=len(chunks),
        storage_dir=storage_path,
        manifest_path=manifest_path,
    )
