# DocBot

DocBot is a local retrieval-augmented generation (RAG) support bot for product documentation. It indexes Markdown and text files from `docs/`, finds relevant passages for a question, then asks Groq's Llama 3.3 70B model to answer using those passages. The API and browser interface run on your machine; this project is not deployed.

## Architecture

```text
docs/*.md, *.txt
      |
      v
ingest.py -> split into chunks -> embed with all-MiniLM-L6-v2 -> persistent ChromaDB
                                                               |
Browser -> FastAPI /ask -> embed question -> retrieve top 4 chunks
                                      -> prompt with context -> Groq Llama 3.3 70B
                                      -> answer + source chunks -> browser
```

## Run locally

1. Use Python 3.11 or newer, then create and activate a virtual environment:

   ```bash
   cd ~/DocBot
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and add your Groq API key:

   ```bash
   cp .env.example .env
   # Edit .env and set GROQ_API_KEY=your_key
   ```

4. Build the local document index (this downloads the embedding model the first time):

   ```bash
   python ingest.py
   ```

5. Start the API and UI:

   ```bash
   uvicorn app:app --reload
   ```

6. Open <http://127.0.0.1:8000>. Ask a question in the page or POST `{"question":"..."}` to `/ask`. The `/health` endpoint reports whether the API process responds. To check answer quality against the sample docs, run `python eval.py` while the server is running.

## Design choices

- **500 character chunks with 50 character overlap:** small chunks keep retrieval focused, while overlap preserves a little context at boundaries. The splitter prefers paragraph and sentence ends and only splits long sentences on whitespace.
- **all-MiniLM-L6-v2 embeddings:** this compact sentence-transformers model produces useful semantic vectors locally, so documents and questions can match by meaning rather than exact wording.
- **Persistent ChromaDB:** the vector index stays on disk in `chroma_db/`, avoiding a rebuild on every server start. Running `ingest.py` deletes and rebuilds the collection so edited or removed docs do not leave stale entries.
- **Top four retrieved chunks:** a small context gives the language model relevant evidence without sending every document for each question. Returned sources let the user inspect that evidence.
- **Context-only system prompt:** it instructs the model to say “I don't know based on the available docs” if the retrieved text does not support an answer, and to name the source files. This reduces unsupported answers, but does not guarantee they never happen.
- **Temperature 0.2:** a low setting favors consistent, focused support answers while still allowing natural wording.
- **One embedding model at app startup:** the model is reused for each request instead of loaded repeatedly, reducing request latency and memory churn.

## Limitations and next steps

- Local only; it is **not deployed** and is intended as a learning/demo project.
- No authentication or authorization; anyone who can reach the local server can ask questions.
- Basic character-based chunk sizing and semantic retrieval; tables and complex document structure are not specially handled.
- No reranking, conversation memory, or citations verified at sentence level.
- The context-only prompt is guidance, not a formal guarantee that the model cannot hallucinate.
- The demo docs and Orbit domain are fictional. Replace them with authorized, current support documents before using this for real product support.
