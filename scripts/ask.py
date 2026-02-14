from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.app.rag.chain import build_chain


def main() -> None:
    load_dotenv(ROOT / ".env")

    if len(sys.argv) < 2:
        print('Usage: python scripts/ask.py "Question..."')
        raise SystemExit(1)
    
    question = sys.argv[1]
    chain = build_chain()
    output = chain.invoke(question)
    print(output)


if __name__ == "__main__":
    main()