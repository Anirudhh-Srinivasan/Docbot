"""Evaluate real retrieval on an isolated sample index, optionally exercise Groq."""
import argparse
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from app import FALLBACK, ChatRequest, app, chat
from ingest import DOCS_DIR, Index

# Expected passage must match BOTH source filename and a literal supporting fact.
CASES = [
    ("How long does a workspace invitation last?", "getting-started", "7 days"),
    ("When are weekly summaries sent?", "getting-started", "Monday"),
    ("How many active projects can a free workspace have?", "getting-started", "2 active projects"),
    ("How long is the new workspace trial?", "getting-started", "14-day"),
    ("What does Team cost per member?", "pricing-and-billing", "$12"),
    ("What discount is there for annual billing?", "pricing-and-billing", "15%"),
    ("How much file storage does Team include?", "pricing-and-billing", "10 GB"),
    ("When does a downgrade take effect?", "pricing-and-billing", "next renewal"),
    ("Which permission is needed to sync GitHub issues?", "troubleshooting", "Issues permission"),
    ("How quickly does GitHub sync retry after reconnecting?", "troubleshooting", "10 minutes"),
    ("Which plan includes SSO for sign-in?", "troubleshooting", "Business"),
    ("How many API requests can I send per minute?", "api-usage", "120"),
    ("How many items can a list endpoint return per page?", "api-usage", "50"),
    ("What HTTP status does a successful issue creation return?", "api-usage", "201"),
    ("Where is workspace data hosted?", "security-and-privacy", "Northern Virginia"),
    ("How long are encrypted backups retained?", "security-and-privacy", "30 days"),
    ("Which encryption is used at rest?", "security-and-privacy", "AES-256"),
]
UNKNOWN = ["How much does Orbit charge for SMS alerts?", "What is the Android app download size?"]


def supported(rows, filename, fact):
    return any(r["filename"] == filename + ".md" and fact.lower() in r["text"].lower() for r in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", action="store_true", help="also send 19 questions to Groq")
    args = parser.parse_args()
    if args.answers and not os.getenv("GROQ_API_KEY", "").strip():
        parser.error("--answers requires GROQ_API_KEY")
    hits = grounded = abstained = errors = 0
    with TemporaryDirectory() as tmp:
        index = Index(Path(tmp))
        for doc in sorted(DOCS_DIR.glob("*.md")):
            index.add("eval", doc.name, doc.read_text("utf-8"))
        app.state.index = index
        for question, filename, fact in CASES:
            hit = supported(index.search("eval", question), filename, fact)
            hits += hit
            print("HIT " if hit else "MISS", question)
            if args.answers:
                try:
                    result = chat(ChatRequest(site_id="eval", question=question))
                    ok = fact.lower() in result["answer"].lower() and supported(result["sources"], filename, fact)
                    grounded += ok
                    print("  ", "PASS" if ok else "REVIEW", result["answer"])
                except Exception as exc:
                    errors += 1
                    print("   ERROR", exc)
        if args.answers:
            for question in UNKNOWN:
                try:
                    result = chat(ChatRequest(site_id="eval", question=question))
                    abstained += result == {"answer": FALLBACK, "sources": []}
                    print(question, result["answer"])
                except Exception as exc:
                    errors += 1
                    print("ERROR", exc)
    print(f"Evidence hit@4: {hits}/{len(CASES)} ({hits / len(CASES):.1%})")
    if args.answers:
        print(f"Answer + cited fact match: {grounded}/{len(CASES)}; abstention: {abstained}/2; provider errors: {errors}")
    else:
        print("Answer grounding and abstention skipped (enable with --answers)")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
