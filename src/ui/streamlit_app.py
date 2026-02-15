from __future__ import annotations

from typing import List, Dict, Tuple

import streamlit as st

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.ui.api_client import invoke_chat, stream_chat

st.set_page_config(page_title="Promtior RAG Chat", page_icon="🤖", layout="centered")
st.title("Promtior RAG Chat")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

def split_sources(text: str) -> Tuple[str, List[str]]:
    marker ="\nSources:"
    if marker not in text:
        return text, []
    main, sources_block = text.split(marker, 1)
    lines = [line.strip() for line in sources_block.splitlines()]
    urls = [lines[2:].strip() for line in lines if line.startswith("- ")]
    return main.strip(), urls

st.sidebar.header("Controls")
use_stream = st.sidebar.checkbox("Use streaming (if available)", value=False)
if st.sidebar.button("Clear conversation"):
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Type your question...")

if prompt:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking...")

        try:
            if use_stream:
                chunks = []
                for token in stream_chat(prompt):
                    chunks.append(token)
                    placeholder.markdown("".join(chunks))
                answer_text = "".join(chunks).strip()
                if not answer_text:
                    answer_text = invoke_chat(prompt)
            else:
                answer_text = invoke_chat(prompt)

            main_text, sources = split_sources(answer_text)
            placeholder.markdown(main_text)

            if sources:
                with st.expander("Sources"):
                    for url in sources:
                        st.markdown(f"- {url}")
        
        except Exception as ex:
            st.error(f"Error: {ex}")
            answer_text = f"Error: {ex}"

    st.session_state["messages"].append({"role": "assistant", "content": answer_text})   