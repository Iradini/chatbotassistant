from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List

from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma, FAISS
from langchain_core.runnables import RunnableLambda
from langchain_ollama import OllamaEmbeddings, OllamaLLM

ENV_BASE_URL = "OLLAMA_BASE_URL"
ENV_LLM_MODEL = "OLLAMA_LLM_MODEL"
ENV_EMBED_MODEL = "OLLAMA_EMBED_MODEL"
ENV_VECTORSTORE_DIR = "VECTORSTORE_DIR"
ENV_VECTORSTORE_IMPL = "VECTORSTORE_IMPL"

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_LLM_MODEL = "llama2"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_VECTORSTORE_DIR = "./storage"
DEFAULT_VECTORSTORE_IMPL = "faiss"

TOP_K = 5

PROMPT_TEMPLATE = """Your are an assistant that answers ONLY using the provided context.
Respond in the same language as the question.
If the context does NOT support the answer, respond EXACTLY:
I did not find that information in the indexed sources. 

Context:
{context}

Question:
{question}

Answer:"""


def _get_env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()

def _get_embeddings() -> OllamaEmbeddings:
    base_url = _get_env(ENV_BASE_URL, DEFAULT_BASE_URL)
    embed_model = _get_env(ENV_EMBED_MODEL, DEFAULT_EMBED_MODEL)
    if not base_url:
        raise ValueError("OLLAMA_BASE_URL is empty.")
    if not embed_model:
        raise ValueError("OLLAMA_EMBED_MODEL is empty.")
    return OllamaEmbeddings(model=embed_model, base_url=base_url)

def _load_vectorstore() -> object:
    impl = _get_env(ENV_VECTORSTORE_IMPL, DEFAULT_VECTORSTORE_IMPL).lower()
    dir_path = Path(_get_env(ENV_VECTORSTORE_DIR, DEFAULT_VECTORSTORE_DIR))
    if not dir_path.exists():
        raise FileNotFoundError(
            f"Vectorstore directory does not exist: {dir_path}"
        )
    
    embeddings = _get_embeddings()

    if impl == "faiss":
        return FAISS.load_local(
            str(dir_path),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    if impl == "chroma":
        return Chroma(
            persist_directory=str(dir_path),
            embedding_function=embeddings,
        )
    raise ValueError("VECTORSTORE_IMPL must be 'faiss' or 'chroma'.")


def _unique_sources(docs: Iterable) -> List[str]:
    seen = set()
    sources: List[str] = []
    for doc in docs:
        source = doc.metadata.get("source")
        if source and source not in seen:
            seen.add(source)
            sources.append(source)
    return sources

def build_chain():
    vectorstore = _load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    llm = OllamaLLM(
        model =_get_env(ENV_LLM_MODEL, DEFAULT_LLM_MODEL),
        temperature=0,
        base_url=_get_env(ENV_BASE_URL, DEFAULT_BASE_URL),
    )

    def _invoke(input_data):
        question = input_data["question"] if isinstance(input_data, dict) else str(input_data)
        docs = retriever.invoke(question)

        if not docs:
            return "I did not find that information in the indexed sources."
        
        context = "\n\n".join(
            doc.page_content for doc in docs if getattr(doc, "page_content", None)
        ).strip()

        if not context:
            return "I did not find that information in the indexed sources."
        
        sources = _unique_sources(docs)
        if not sources:
            return "I did not find that information in the indexed sources."
        
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)
        answer = llm.invoke(prompt)

        answer_text = answer.strip() if isinstance(answer, str) else str(answer).strip()
        sources_block = "\n".join(f"- {url}" for url in sources)
        return f"{answer_text}\n\nSources:\n{sources_block}"
    
    return RunnableLambda(_invoke)
