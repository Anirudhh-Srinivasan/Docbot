# V1 decisions

- Keep the existing 500-character target and 50-character overlap, preferring paragraph and sentence boundaries so chunks stay short even with unbroken input.
- Use one cosine Chroma collection per public site ID and one backend-only admin key per site to keep customer writes isolated.
- Use immutable document IDs derived from name and content so identical imports are idempotent and a failed revision leaves the previous document searchable. Delete the old revision explicitly.
- Use new collection names and re-import the source files so the prototype index remains recoverable.
- Accept raw file bodies with a filename query parameter so uploads can be size-checked as they arrive without extra multipart dependencies.
- Extract PDF text with Poppler and fetch a single final HTTP(S) URL with curl pinned to a validated public IPv4 address to bound the importer.
- Return complete JSON after checking citation IDs. Defer token streaming because partial answers would reach readers before citation validation.
- Use one process and a fixed per-IP minute window because the embedded database and rate counters live on one machine.
