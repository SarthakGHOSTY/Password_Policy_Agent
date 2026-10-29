import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import accounts
import agent
import config
import tools

STATIC = Path(__file__).parent / "static"
TYPES = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}
assistant = agent.Agent()
lock = threading.Lock()


def state():
    return {
        "key_set": not config.GROQ_API_KEY.startswith("PASTE"),
        "model": config.MODELS[0],
        "accounts": [accounts.describe(user) for user in accounts.ACCOUNTS],
        "audit": agent.AUDIT[-100:],
        "tools": [{"name": name, "description": description, "confirm": name in tools.NEEDS_CONFIRMATION,
                   "read_only": name in tools.READ_ONLY} for name, (_, description) in tools.TOOLS.items()],
    }


class Handler(BaseHTTPRequestHandler):
    def reply(self, data, content_type="application/json"):
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/state":
            return self.reply(state())
        file = STATIC / ("index.html" if self.path == "/" else self.path.lstrip("/"))
        if file.resolve().parent != STATIC.resolve() or not file.is_file():
            return self.send_error(404)
        self.reply(file.read_bytes(), TYPES.get(file.suffix, "text/plain"))

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        data = json.loads(self.rfile.read(length) or "{}")
        with lock:
            if self.path == "/api/chat":
                return self.reply(assistant.chat(str(data.get("message", ""))[:1000]))
            if self.path == "/api/confirm":
                return self.reply(assistant.confirm(bool(data.get("approved"))))
            if self.path == "/api/reset":
                assistant.reset()
                return self.reply({"ok": True})
        self.send_error(404)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    url = f"http://127.0.0.1:{config.PORT}"
    print(f"Password agent running at {url}  (Ctrl+C to stop)")
    threading.Timer(1, webbrowser.open, [url]).start()
    ThreadingHTTPServer(("127.0.0.1", config.PORT), Handler).serve_forever()
