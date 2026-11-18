# DocBot status

## Review of the supplied prototype, before v1 changes

- Ran the original ingestion CLI against a temporary copy. Five fictional Orbit files produced 16 real MiniLM chunks in persistent Chroma. Loaded the supplied index and retrieved pricing-and-billing.md chunk 0 for “What is Team pricing?”
- Ran FastAPI startup and route handlers. Health returned ok, the home handler resolved the static page, a blank question returned 400 and a normal question returned 503 because the Groq key was empty. The original six-case HTTP eval scored 0/6 due to blocked local sockets. No live Groq answer or browser interaction was verified.
- The single-page HTML client posts to /ask and renders escaped answers and expandable chunks. The Python code calls the real SDK. No canned answer path was found. The Orbit name, plans, support addresses and example domain are sample content. The prompt, branding, collection, paths, model IDs and localhost eval target are hardcoded.
- The original “sources” are all top-four candidates regardless of which evidence the answer uses. The eval matches answer keywords only. The splitter loses overlap in its long-sentence path and can exceed its target. Reindexing deletes the collection before embedding succeeds. A running app can retain an absent or stale collection handle.
- Missing: upload, PDF extraction, URL scraping, site isolation, document management, /chat, streaming, embed loader, explicit cross-origin configuration, rate limiting, automated tests, retrieval metrics, deployment files and a demo GIF placeholder.
- All seven direct dependencies have callers. No dead source module identified. The local virtualenv, bytecode and 17 MB generated index are runtime artifacts. Old Chroma printed telemetry-client compatibility errors but indexing and search succeeded.
- The supplied .git directory is empty and read-only in this workspace. Historical branches and tracked-file status could not be audited. Feature commits use a separate Git directory based on a snapshot of the supplied source.

## V1 implementation and verification

| Area | Implemented and exercised | Remaining limits |
| --- | --- | --- |
| Ingestion | Seeded five local Orbit files into the new site collection (17 chunks). Tested raw file upload, UTF-8 parsing, bounded overlap, duplicate upload, empty/invalid input and 2 MB limit. A real PDF uploaded through FastAPI produced a searchable chunk. | Text-layer PDFs only. Changed content creates a new revision. Delete the old ID when replacing it. |
| URL import | Exercised the API, real HTML parsing, chunking and indexing using a controlled DNS/HTTP result. Rejected private addresses and unsupported schemes. | Public DNS resolution failed here. A live remote import still needs a smoke test. Single final URL, public IPv4 and UTF-8 only. |
| Tenancy and admin | Real Chroma and MiniLM in temporary storage. Exercised two populated sites, separate admin keys, list, delete, and empty-site lookup. | Chat is public per site. Publish only support docs intended for visitors. |
| Chat and citations | Tested the HTTP contract, top-four retrieval, provider failure, citation bounds, refusal and missing key. The success test exercises the Groq SDK using a simulated HTTP response. | No Groq key available. Live Llama output and hallucination rate are unverified. Token streaming deferred so citations can be checked before display. |
| Widget | Preserved the existing plain-JS chat UI. Added a script loader, floating toggle, responsive iframe and demo. Verified served assets, client syntax, and mount/open/close with a simulated DOM in Node. | Chrome and Firefox failed to start in the sandbox. Real cross-origin browser behavior, mobile layout and keyboard interaction still need a device/browser check. |
| Limits and errors | Exercised per-IP 429 and Retry-After, allowed and denied CORS preflights, frame policy, 403, 404, 413, 422, 502 and 503. | Single-process rate windows. Proxy configuration determines whether visitors share an IP bucket. |
| Evaluation | Real sample retrieval hit@4 was **17/17**. The answer mode checks the literal expected fact in both reply and cited evidence and checks two unanswerable questions. | Sample-only result. No live answer or abstention score. |
| Delivery | Added setup, API and embed examples, architecture, GIF placeholder, Dockerfile, Vercel static build and decision log. Ran Node demo build, Python compilation, JS syntax checks, and Uvicorn startup. FastAPI health, demo, widget, chat page, OpenAPI and Swagger UI returned 200 via in-process HTTP. | Docker daemon access and outbound/loopback client sockets are restricted. No image build, hosted deployment, or fresh-install time measurement. |

The three unittest methods include a full API lifecycle with the real index. They passed in the supplied Linux virtualenv. The offline model cache supports tests without credentials. Chroma 1.0.8 emits nonfatal telemetry SDK signature errors with the supplied PostHog version even when telemetry is disabled.

The portable Git history is in `docbot-v1.bundle`. It starts with a snapshot of the supplied source followed by the review and feature commits. Run `git clone docbot-v1.bundle docbot-v1-checkout` to obtain a normal checkout. The bundle excludes secrets, generated indexes and the virtualenv.

## Next validation and v2

Add a backend Groq key and run `python eval.py --answers`. Inspect the cited evidence, especially for plausible questions the docs cannot answer. Try a real public URL and the widget on a phone from an allowed host. For v2, build a small held-out set from actual support questions and tune retrieval or abstention against observed failures.
