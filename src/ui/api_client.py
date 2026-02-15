from __future__ import annotations

import json
import os 
from typing import Iterator, Optional

import requests

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 300

ENV_BASE_URL = "LANGSERVE_BASE_URL"

def _base_url() -> str:
    return os.getenv(ENV_BASE_URL, DEFAULT_BASE_URL).rstrip("/")

def _extract_output(data) -> str:
    if isinstance(data, dict):
        if "output" in data:
            return str(data["output"])
        if "answer" in data:
            return str(data["answer"])
    if isinstance(data, list):
        return "\n".join(str(x) for x in data)
    return str(data)

def invoke_chat(question: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    url = f"{_base_url()}/chat/invoke"

    payload = {"input": {"question": question}}
    resp = requests.post(url, json=payload, timeout=timeout)

    if resp.status_code == 422:
        payload = {"input": question}
        resp = requests.post(url, json=payload, timeout=(10, 600))

    resp.raise_for_status()
    data = resp.json()
    return _extract_output(data)

def stream_chat(question: str, timeout: int = DEFAULT_TIMEOUT) -> Iterator[str]:
    url = f"{_base_url()}/chat/stream"
    headers = {"Accept": "text/event-stream"}

    payload = {"input": {"question": question}}
    with requests.post(url, json=payload, headers=headers, stream=True, timeout=(10, 600)) as resp:
        if resp.status_code == 404:
            raise RuntimeError("Streaming endpoint not available.")
        if resp.status_code == 422:
            payload = {"input": question}
            resp = requests.post(url, json=payload, headers=headers, stream=True, timeout=timeout)

        resp.raise_for_status()

        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8")
            if not line.startswith("data: "):
                continue

            data = line[6:].strip()
            if data == "[DONE]":
                break

            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                yield data
                continue

            if isinstance(obj, str):
                yield obj
                continue

            if isinstance(obj, dict):
                chunk = (
                    obj.get("output")
                    or obj.get("chunk")
                    or obj.get("delta")
                    or obj.get("text")
                )
                if isinstance(chunk, dict):
                    chunk = chunk.get("content") or chunk.get("text") or ""
                if chunk:
                    yield str(chunk)