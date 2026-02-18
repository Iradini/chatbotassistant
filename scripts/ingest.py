from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.app.ingest.loader import DEFAULT_SEEDS, load_urls, load_presentation_pdf
from src.app.ingest.indexer import index_documents


def main() -> None:
    load_dotenv(ROOT / ".env")

    storage_dir = os.getenv("VECTORSTORE_DIR")
    if storage_dir:
        storage_dir = Path(storage_dir)
    else: 
        storage_dir = ROOT / "storage"

    try:
        web_docs = load_urls(DEFAULT_SEEDS)

        presentation_path = os.getenv("PRESENTATION_PATH", "").strip()


        if presentation_path:
            print(f"Loading presentation from: {presentation_path}")
            if not os.path.isfile(presentation_path):
                raise FileNotFoundError(f"PRESENTATION_PATH does not exist: {presentation_path}")
    
            pdf_docs = load_presentation_pdf(presentation_path)
        else:
            pdf_docs = []
            
        docs = web_docs + pdf_docs

        print(f"Total documents before chunking: {len(docs)}")

        stats = index_documents(
            docs=docs,
            seeds=DEFAULT_SEEDS,
            storage_dir=storage_dir,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc

    print("Ingestion complete.")
    print(f"Documents: {stats.doc_count}")
    print(f"Chunks: {stats.chunk_count}")
    print(f"Vector store: {stats.storage_dir}")
    print(f"Manifest: {stats.manifest_path}")


if __name__ == "__main__":
    main()