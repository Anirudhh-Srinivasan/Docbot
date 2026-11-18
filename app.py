"""FastAPI endpoints for asking questions over the locally indexed documents."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "docbot_documents"
TOP_K = 4
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL_NAME = "llama-3.3-70b-versatile"
TEMPERATURE = 0.2
MAX_QUESTION_LENGTH = 2000
load_dotenv(BASE_DIR / ".env")

SYSTEM_PROMPT = """You are Orbit's documentation support assistant. Answer only using the supplied document context. If the context does not contain the answer, say exactly: "I don't know based on the available docs." Do not guess or add outside facts. When you answer, name the source file or files you used."""


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Load reusable local models and the persistent collection once at startup."""
    application.state.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)
    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        application.state.collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        application.state.collection = None
    yield


app = FastAPI(title="DocBot", description="Local documentation question answering", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class AskRequest(BaseModel):
    question: str


@app.get("/")
def home() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask")
def ask(request: AskRequest) -> dict:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please enter a question.")
    if len(question) > MAX_QUESTION_LENGTH:
        raise HTTPException(status_code=400, detail=f"Question must be at most {MAX_QUESTION_LENGTH} characters.")
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is missing. Add it to your .env file and restart DocBot.")

    collection = getattr(app.state, "collection", None)
    if collection is None or collection.count() == 0:
        raise HTTPException(status_code=503, detail="The document index is empty. Run `python ingest.py` first.")

    try:
        embedding = app.state.embedder.encode(question).tolist()
        results = collection.query(query_embeddings=[embedding], n_results=min(TOP_K, collection.count()), include=["documents", "metadatas", "distances"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not search the local document index: {exc}") from exc

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    context = "\n\n".join(
        f"[Source file: {meta.get('filename', 'unknown')}, chunk {meta.get('chunk_index', '?')}]\n{text}"
        for text, meta in zip(documents, metadatas)
    )
    try:
        response = Groq(api_key=api_key).chat.completions.create(
            model=LLM_MODEL_NAME,
            temperature=TEMPERATURE,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Document context:\n{context}\n\nQuestion: {question}"},
            ],
        )
        answer = response.choices[0].message.content
        if not answer:
            raise ValueError("Groq returned an empty answer")
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Groq could not answer right now. Check your API key and connection, then try again.") from exc

    sources = [
        {"filename": meta.get("filename", "unknown"), "chunk_index": meta.get("chunk_index"), "text": text, "score": round(1 - float(distance), 4)}
        for text, meta, distance in zip(documents, metadatas, distances)
    ]
    return {"answer": answer, "sources": sources}
