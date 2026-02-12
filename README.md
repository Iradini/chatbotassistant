# CHATBOT ASSISTANT

Minimal scaffold for a RAG chatbot with LangChain + LangServer

### Requirements

- Python 3.11

#### Create environment (venv)

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version

#### Create environment (conda)

conda create -n protiorchatbot python=3.11
conda activate protiorchatbot
python --version

## Install dependencies

python -m pip install -r requirements.txt

## Configuration

copy .env.example .env

## Execute

uvicorn src.app.main:app --reload

## Health check

http://127.0.0.1:8000/health
