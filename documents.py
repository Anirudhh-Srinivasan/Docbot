"""Bounded text extraction and single-page public HTML import."""
import ipaddress
import socket
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

MAX_BYTES = 2_000_000


def extract(filename, data):
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF header")
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp, "source.pdf"), Path(tmp, "text")
            src.write_bytes(data)
            # Separate process bounds CPU, memory and expanded output on Linux.
            result = subprocess.run(
                ["prlimit", "--cpu=10", "--as=536870912", "--fsize=2000000", "--",
                 "pdftotext", "-enc", "UTF-8", str(src), str(dst)],
                capture_output=True, timeout=15,
            )
            if result.returncode:
                raise ValueError("Could not extract PDF text")
            data = dst.read_bytes()
    elif suffix not in {".txt", ".md"}:
        raise ValueError("Use a PDF, TXT or MD file")
    if b"\0" in data:
        raise ValueError("Expected UTF-8 text")
    return data.decode("utf-8-sig")


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "head", "noscript", "template"}:
            self.hidden += 1
        if tag in {"p", "div", "li", "h1", "h2", "h3", "br", "section"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "head", "noscript", "template"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def fetch_page(url):
    parts = urlsplit(url)
    host = parts.hostname or ""
    if (parts.scheme not in {"http", "https"} or parts.username is not None
            or parts.password is not None or parts.port not in {None, 80, 443}
            or not host or not host.isascii() or not all(c.isalnum() or c in ".-" for c in host)
            or any(c.isspace() or ord(c) < 32 or c == "\\" for c in url)):
        raise ValueError("Use a public HTTP(S) hostname on a standard port")
    port = parts.port or (443 if parts.scheme == "https" else 80)
    try:
        addresses = [ipaddress.ip_address(row[4][0]) for row in
                     socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)]
    except OSError as exc:
        raise ValueError("Could not resolve URL hostname") from exc
    if not addresses or any(not ip.is_global or ip.is_multicast for ip in addresses):
        raise ValueError("URL must resolve to a public address")
    # Pin the checked address, bypass proxies and reject redirects.
    with tempfile.TemporaryDirectory() as tmp:
        body = Path(tmp, "page")
        result = subprocess.run(
            ["curl", "-q", "--globoff", "--silent", "--noproxy", "*", "--max-time", "12",
             "--max-filesize", str(MAX_BYTES), "--resolve", f"{host}:{port}:{addresses[0]}",
             "--output", str(body), "--write-out", "%{http_code} %{content_type}", "--", url],
            capture_output=True, timeout=15,
        )
        status, _, mime = result.stdout.decode(errors="replace").partition(" ")
        if result.returncode or status != "200":
            raise ValueError("Could not fetch page. Supply its final public URL")
        if mime.split(";")[0].strip().lower() not in {"text/html", "text/plain"}:
            raise ValueError("URL must return HTML or plain text")
        if body.stat().st_size > MAX_BYTES:
            raise ValueError("Page is too large")
        text = body.read_text("utf-8-sig")
        if mime.lower().startswith("text/html"):
            parser = PageText()
            parser.feed(text)
            parser.close()
            text = "".join(parser.parts)
        return text
