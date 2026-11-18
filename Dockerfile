FROM python:3.11-slim-bookworm
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2 CHROMA_PATH=/data/chroma
RUN apt-get update && apt-get install -y --no-install-recommends curl poppler-utils util-linux libgomp1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.6.0 && pip install -r requirements.txt
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
ENV HF_HUB_OFFLINE=1
COPY app.py ingest.py documents.py ./
COPY static static
COPY docs docs
CMD ["sh", "-c", "exec python -m uvicorn app:app --host 0.0.0.0 --port \"\${PORT:-8000}\" --workers 1"]
