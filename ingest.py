"""Build a persistent Chroma index from the Markdown and text files in docs/."""

from pathlib import Path
import re

import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "docbot_documents"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500  # target characters per chunk
CHUNK_OVERLAP = 50  # characters repeated from the previous chunk


def split_into_chunks(text: str) -> list[str]:
    """Make roughly CHUNK_SIZE character chunks, preferring paragraph/sentence ends."""
    text = text.strip()
    if not text:
        return []

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    chunks: list[str] = []
    current = ""

    def save_current() -> None:
        nonlocal current
        if current:
            chunks.append(current.strip())
            current = ""

    for paragraph in paragraphs:
        # A long paragraph can still be split at sentence boundaries.
        pieces = re.split(r"(?<=[.!?])\s+", paragraph)
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            if len(piece) > CHUNK_SIZE:
                save_current()
                # Last-resort split on whitespace; words themselves stay intact.
                words, segment = piece.split(), ""
                for word in words:
                    if segment and len(segment) + 1 + len(word) > CHUNK_SIZE:
                        chunks.append(segment)
                        segment = ""
                    segment = f"{segment} {word}".strip()
                if segment:
                    current = segment
            elif current and len(current) + 2 + len(piece) > CHUNK_SIZE:
                previous = current
                save_current()
                # Small tail overlap preserves context at the chunk boundary.
                overlap = previous[-CHUNK_OVERLAP:].lstrip()
                current = f"{overlap} {piece}".strip()
            else:
                current = f"{current}\n\n{piece}".strip()
        # Keep paragraph boundaries; the next paragraph is added like a sentence.
    save_current()
    return chunks


def main() -> None:
    files = sorted([*DOCS_DIR.rglob("*.md"), *DOCS_DIR.rglob("*.txt")])
    client = chromadb.PersistentClient(path=str(DB_DIR))
    # Delete first so edits and removed files never leave stale vectors behind.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    # Cosine distance fits normalized sentence embeddings; 1 - distance is a
    # readable similarity score in the API response.
    collection = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    documents: list[str] = []
    metadatas: list[dict[str, str | int]] = []
    ids: list[str] = []
    for file_path in files:
        for chunk_index, chunk in enumerate(split_into_chunks(file_path.read_text(encoding="utf-8"))):
            documents.append(chunk)
            metadatas.append({"filename": file_path.relative_to(DOCS_DIR).as_posix(), "chunk_index": chunk_index})
            ids.append(f"{len(ids)}")

    if documents:
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        embeddings = model.encode(documents, convert_to_numpy=True).tolist()
        collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    print(f"Stored {len(documents)} chunks from {len(files)} files in {DB_DIR}")


if __name__ == "__main__":
    main()
