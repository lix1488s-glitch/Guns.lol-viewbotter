"""Minimal stdlib-only dev server for the Guns.lol Killa Script project page.

Serves a single landing page that renders the repository README plus a small
JSON status endpoint. No third-party dependencies so it boots offline.
"""

import html
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "3000"))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(REPO_ROOT, "README.md")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Guns.lol Killa Script</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #0e1116;
    color: #e6edf3;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
  }}
  main {{ max-width: 820px; margin: 0 auto; padding: 48px 24px 80px; }}
  header {{ border-bottom: 1px solid #262c36; padding-bottom: 24px; margin-bottom: 32px; }}
  .badge {{
    display: inline-block; padding: 4px 10px; border-radius: 999px;
    background: #1f6feb22; color: #79c0ff; border: 1px solid #1f6feb55;
    font-size: 12px; letter-spacing: .04em; text-transform: uppercase;
  }}
  h1 {{ font-size: 32px; margin: 16px 0 8px; }}
  p.sub {{ margin: 0; color: #9198a1; }}
  section h2 {{ font-size: 20px; margin: 32px 0 8px; }}
  ul {{ padding-left: 20px; }}
  li {{ margin: 6px 0; }}
  code {{
    background: #161b22; border: 1px solid #262c36; border-radius: 6px;
    padding: 2px 6px; font-size: 13px;
  }}
  .readme {{
    background: #161b22; border: 1px solid #262c36; border-radius: 12px;
    padding: 20px 24px; white-space: pre-wrap; font-size: 14px; color: #c9d1d9;
  }}
  footer {{ margin-top: 40px; color: #6e7681; font-size: 13px; }}
</style>
</head>
<body>
<main>
  <header>
    <span class="badge">Revived</span>
    <h1>Guns.lol Killa Script</h1>
    <p class="sub">Python backend &middot; Electron desktop client &middot; dev preview</p>
  </header>

  <section>
    <h2>Repository contents</h2>
    <ul>
      <li><code>DowngradeChrome(REQUIRED).py</code> &mdash; Windows-only Chrome downgrade helper (needs admin, not runnable in this sandbox)</li>
      <li><code>web/server.py</code> &mdash; this dev landing page, stdlib only</li>
      <li><code>docker-compose.alloy.yaml</code> &mdash; Alloy dev stack</li>
    </ul>
  </section>

  <section>
    <h2>Status</h2>
    <ul>
      <li>Web preview: <strong id="status">checking&hellip;</strong></li>
      <li>Listening port: <code>{port}</code></li>
    </ul>
  </section>

  <section>
    <h2>README</h2>
    <div class="readme">{readme}</div>
  </section>

  <footer>Development preview only. The desktop app is closed source per the README.</footer>
</main>
<script>
  fetch('/api/status')
    .then(function (r) {{ return r.json(); }})
    .then(function (d) {{
      document.getElementById('status').textContent = d.status + ' (' + d.service + ')';
    }})
    .catch(function () {{
      document.getElementById('status').textContent = 'unavailable';
    }});
</script>
</body>
</html>
"""


def read_readme() -> str:
    try:
        with open(README_PATH, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return "README.md not found."
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    return html.escape(text.strip())


class Handler(BaseHTTPRequestHandler):
    server_version = "GunsLolDevServer/1.0"

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/api/status":
            payload = json.dumps(
                {"status": "ok", "service": "web", "port": PORT}
            ).encode()
            self._send(200, payload, "application/json; charset=utf-8")
            return
        if path in ("/", "/index.html"):
            page = PAGE.format(readme=read_readme(), port=PORT)
            self._send(200, page.encode(), "text/html; charset=utf-8")
            return
        self._send(404, b"Not Found", "text/plain; charset=utf-8")

    def log_message(self, fmt: str, *args) -> None:
        print("[web] " + (fmt % args), flush=True)


if __name__ == "__main__":
    print(f"[web] serving on http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
