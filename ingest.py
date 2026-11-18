"""Local MiniLM embeddings and a persistent cosine collection per public site."""
import argparse
import hashlib
import os
import re
from pathlib import Path

import chromadb
from chromadb.errors import NotFoundError
from chromadb.config import Settings
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
load_dotenv(BASE_DIR / ".env")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
SITE_PATTERN = r"[a-z0-9][a-z0-9-]{0,47}"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def split_into_chunks(text: str) -> list[str]:
    text = text.strip()
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            floor = start + CHUNK_SIZE // 2
            for boundary in ("\n\n", ". ", "\n", " "):
                pos = text.rfind(boundary, floor, end)
                if pos >= floor:
                    end = pos + len(boundary)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = end - CHUNK_OVERLAP
    return chunks


class Index:
    def __init__(self, directory=None):
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")
        self.client = chromadb.PersistentClient(
            path=str(directory or os.getenv("CHROMA_PATH") or BASE_DIR / "chroma_db"),
            settings=Settings(anonymized_telemetry=False),
        )

    def collection(self, site, create=False):
        if not re.fullmatch(SITE_PATTERN, site):
            raise ValueError("Invalid site ID")
        name = f"docbot-site-{site}"
        if create:
            return self.client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})
        try:
            return self.client.get_collection(name)
        except NotFoundError:
            return None

    def add(self, site, filename, text):
        if len(text) > 500_000:
            raise ValueError("Document exceeds 500,000 extracted characters")
        chunks = split_into_chunks(text)
        if not chunks:
            raise ValueError("Document contains no readable text")
        doc_id = hashlib.sha256((filename + "\0" + text).encode()).hexdigest()
        collection = self.collection(site, create=True)
        ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
        if not collection.get(ids=[ids[0]], include=[])["ids"]:
            collection.upsert(
                ids=ids, documents=chunks,
                embeddings=self.model.encode(chunks).tolist(),
                metadatas=[dict(document_id=doc_id, filename=filename, chunk_index=i)
                           for i in range(len(chunks))],
            )
        return dict(document_id=doc_id, filename=filename, chunks=len(chunks))

    def search(self, site, question, k=4):
        collection = self.collection(site)
        count = collection.count() if collection is not None else 0
        if not count:
            return []
        result = collection.query(query_embeddings=[self.model.encode(question).tolist()],
                                  n_results=min(count, k), include=["documents", "metadatas", "distances"])
        return [dict(**meta, text=text, score=round(1 - distance, 4))
                for meta, text, distance in zip(result["metadatas"][0], result["documents"][0],
                                                result["distances"][0])]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="orbit")
    args = parser.parse_args()
    index = Index()
    for path in sorted(DOCS_DIR.rglob("*")):
        if path.suffix.lower() in {".md", ".txt"}:
            print(index.add(args.site, path.relative_to(DOCS_DIR).as_posix(), path.read_text("utf-8")))


if __name__ == "__main__":
    main()
