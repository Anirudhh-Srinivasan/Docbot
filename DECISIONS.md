# V1 decisions

- Keep the existing 500-character target and 50-character overlap, preferring paragraph and sentence boundaries so chunks stay short even with unbroken input.
- Use one cosine Chroma collection per public site ID and one backend-only admin key per site to keep customer writes isolated.
- Use immutable document IDs derived from name and content so identical imports are idempotent and a failed revision leaves the previous document searchable. Delete the old revision explicitly.
- Use new collection names and re-import the source files so the prototype index remains recoverable.
