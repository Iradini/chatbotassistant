from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader


DEFAULT_SEEDS = [
    "https://www.promtior.ai/",
    "https://www.promtior.ai/service",
]

def fetch_page(url: str, timeout: int = 20) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RAGLoader/1.0; +https://www.promtior.ai/)"
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text   

def extract_title(soup: BeautifulSoup) -> str:
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    return "untitled"

def extract_text(html: BeautifulSoup) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg", "footer", "header", "nav"]):
        tag.decompose()
    
    text = soup.get_text(separator=" ", strip=True)
    text = " ".join(text.split())
    return text

def load_urls(urls: Optional[Iterable[str]] = None) -> List[Document]:
    if urls is None:
        urls = DEFAULT_SEEDS

    documents: List[Document] = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    for url in urls:
        html = fetch_page(url)
        soup = BeautifulSoup(html, "lxml")
        title = extract_title(soup)
        text = extract_text(html)

        doc = Document(
            page_content=text,
            metadata={
                "source": url,
                "fetched_at": fetched_at,
                "title": title,
            },
        )
        documents.append(doc)
    
    return documents

def load_presentation_pdf(pdf_path: str) -> List[Document]:
    path = Path(pdf_path)
    loader = PyPDFLoader(str(path))
    docs = loader.load()

    normalized_docs: List[Document] = []

    for d in docs:
        page_number = d.metadata.get("page", 0)

        normalized_docs.append(
            Document(
                page_content=d.page_content,
                metadata={
                    "source": f"presentation{path.name}#page={page_number + 1}",
                    "source_type": "presentation",
                },
            )
        )

    return normalized_docs