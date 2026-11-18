import os
import socket
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import httpx

from app import FALLBACK, app, lifespan
from documents import PageText, fetch_page
from ingest import split_into_chunks


class Parsing(unittest.TestCase):
    def test_overlap_and_bound(self):
        text = "abcdefghij" * 151
        parts = split_into_chunks(text)
        self.assertTrue(all(len(p) <= 500 for p in parts))
        self.assertEqual(parts[0][-50:], parts[1][:50])
        self.assertEqual(parts[0] + "".join(p[50:] for p in parts[1:]), text)

    def test_url_controls_and_text(self):
        for url in ["file:///etc/passwd", "http://127.0.0.1", "http://user@example.org"]:
            with self.assertRaises(ValueError):
                fetch_page(url)
        parser = PageText()
        parser.feed("<head>title</head><p>support</p><script>alert()</script>")
        self.assertEqual("support", "".join(parser.parts).strip())


class API(unittest.IsolatedAsyncioTestCase):
    async def test_site_lifecycle(self):
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "CHROMA_PATH": tmp, "SITE_ADMIN_KEYS": '{"alpha":"secret","beta":"another"}',
            "GROQ_API_KEY": "test-only", "RATE_LIMIT_PER_MINUTE": "100",
        }):
            async with lifespan(app), httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                docs = "/sites/alpha/documents"
                headers = {"X-Admin-Key": "secret"}
                async def upload(name, body):
                    return await client.post(docs, params={"filename": name}, content=body, headers=headers)
                async def ask(site):
                    return await client.post("/chat", json={"site_id": site, "question": "How long are logs kept?"})
                self.assertEqual((await client.get("/health")).json(), {"status": "ok"})
                home = await client.get("/")
                self.assertIn("frame-ancestors", home.headers["content-security-policy"])
                self.assertIn("text/html", home.headers["content-type"])
                self.assertEqual((await client.get("/static/widget.js")).status_code, 200)
                origin = "https://unlisted.example"
                preflight = await client.options("/chat", headers={
                    "Origin": origin, "Access-Control-Request-Method": "POST",
                })
                self.assertNotIn("access-control-allow-origin", preflight.headers)
                self.assertEqual((await client.get(docs)).status_code, 403)
                self.assertEqual((await client.get("/sites/beta/documents", headers=headers)).status_code, 403)
                self.assertEqual((await upload("bad.pdf", b"oops")).status_code, 422)
                self.assertEqual((await upload("empty.md", b"  ")).status_code, 422)
                self.assertEqual((await upload("big.txt", b"x" * 2_000_001)).status_code, 413)
                first = await upload("policy.md", b"System logs are kept for 30 days.")
                self.assertEqual(first.status_code, 200, first.text)
                doc = first.json()["document_id"]
                self.assertEqual((await upload("policy.md", b"System logs are kept for 30 days.")).json()["document_id"], doc)
                self.assertEqual(len((await client.get(docs, headers=headers)).json()), 1)
                self.assertEqual((await ask("beta")).status_code, 404)
                # Stub only external DNS and curl. Exercise extraction, route and real index.
                def serve_page(command, **kwargs):
                    output = command[command.index("--output") + 1]
                    Path(output).write_text("<p>Beta retains logs for 90 days.</p>")
                    return subprocess.CompletedProcess(command, 0, b"200 text/html", b"")
                with patch("documents.socket.getaddrinfo", return_value=[
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
                ]), patch("documents.subprocess.run", side_effect=serve_page):
                    page = await client.post("/sites/beta/urls", headers={"X-Admin-Key": "another"},
                                             json={"url": "https://example.org/support"})
                    self.assertEqual(page.status_code, 200, page.text)
                self.assertEqual(len(app.state.index.search("alpha", "logs")), 1)
                self.assertIn("90 days", app.state.index.search("beta", "logs")[0]["text"])
                with patch("app.generate", return_value={"answer": "30 days", "citations": [1]}):
                    reply = (await ask("alpha")).json()
                    self.assertEqual(reply["answer"], "30 days")
                    self.assertEqual(reply["sources"][0]["document_id"], doc)
                with patch("app.generate", return_value={"answer": "90 days", "citations": [99]}):
                    self.assertEqual((await ask("alpha")).json(), {"answer": FALLBACK, "sources": []})
                with patch("app.generate", side_effect=TimeoutError):
                    self.assertEqual((await ask("alpha")).status_code, 502)
                self.assertEqual((await client.delete(docs + "/" + doc, headers=headers)).status_code, 200)
                self.assertEqual((await ask("alpha")).status_code, 404)
                app.state.limit = 1
                denied = await ask("alpha")
                self.assertEqual(denied.status_code, 429)
                self.assertIn("retry-after", denied.headers)
