from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.app.ingest.loader import DEFAULT_SEEDS, load_urls
from src.app.ingest.indexer import index_documents


def main() -> None:
    load_dotenv(ROOT / ".env")
    try:
        docs = load_urls(DEFAULT_SEEDS)
        stats = index_documents(
            docs=docs,
            seeds=DEFAULT_SEEDS,
            storage_dir=ROOT / "storage",
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
