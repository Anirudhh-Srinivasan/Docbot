# DocBot status

## Review of the supplied prototype, before v1 changes

- Ran the original ingestion CLI against a temporary copy. Five fictional Orbit files produced 16 real MiniLM chunks in persistent Chroma. Loaded the supplied index and retrieved pricing-and-billing.md chunk 0 for “What is Team pricing?”
- Ran FastAPI startup and route handlers. Health returned ok, the home handler resolved the static page, a blank question returned 400 and a normal question returned 503 because the Groq key was empty. The original six-case HTTP eval scored 0/6 due to blocked local sockets. No live Groq answer or browser interaction was verified.
- The single-page HTML client posts to /ask and renders escaped answers and expandable chunks. The Python code calls the real SDK. No canned answer path was found. The Orbit name, plans, support addresses and example domain are sample content. The prompt, branding, collection, paths, model IDs and localhost eval target are hardcoded.
- The original “sources” are all top-four candidates regardless of which evidence the answer uses. The eval matches answer keywords only. The splitter loses overlap in its long-sentence path and can exceed its target. Reindexing deletes the collection before embedding succeeds. A running app can retain an absent or stale collection handle.
- Missing: upload, PDF extraction, URL scraping, site isolation, document management, /chat, streaming, embed loader, explicit cross-origin configuration, rate limiting, automated tests, retrieval metrics, deployment files and a demo GIF placeholder.
- All seven direct dependencies have callers. No dead source module identified. The local virtualenv, bytecode and 17 MB generated index are runtime artifacts. Old Chroma printed telemetry-client compatibility errors but indexing and search succeeded.
- The supplied .git directory is empty and read-only in this workspace. Historical branches and tracked-file status could not be audited. Feature commits use a separate Git directory based on a snapshot of the supplied source.
