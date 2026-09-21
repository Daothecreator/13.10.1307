"""HTTP API-сервер для базы аудитов ZAFLA — только стандартная библиотека.

Автор: Davyd Kochuhur (Zero Azimuth Vivifactor)

Запуск:
    python src/server.py [--db путь/к/AUDITS_DB.sqlite] [--host 0.0.0.0] [--port 8017]

Эндпоинты (JSON):
    GET /api/stats                      — статистика базы
    GET /api/meta                       — метаданные (авторство, идентификаторы)
    GET /api/search?q=...&limit=&offset= — полнотекстовый поиск FTS5
    GET /api/files?ext=.pdf&limit=&offset= — список документов
    GET /api/file/{id}                  — метаданные документа
    GET /api/file/{id}?text=1           — + дословный и читаемый текст
    GET /api/file/{id}/original         — скачать оригинальный файл (blob)
    GET /api/signatures                 — найденные подписи/имена автора
    GET /api/certifications             — идентификаторы/сертификации ZAFLA
    GET /                               — простая веб-страница с поиском
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

from audits_db import AuditsDB, DEFAULT_DB_PATH

# Windows-консоль может быть в cp1252 — не падаем на кириллице в логах
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

INDEX_HTML = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<title>ZAFLA Audits Database</title><style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}
input{width:70%;padding:.5rem}button{padding:.5rem 1rem}
.hit{border-bottom:1px solid #ddd;padding:.6rem 0}
small{color:#666}</style></head><body>
<h1>ZAFLA Audits Database</h1>
<p><small>© Davyd Kochuhur (Zero Azimuth Vivifactor). 1026 документов, полнотекстовый поиск FTS5.</small></p>
<input id=q placeholder="Поиск: BlackRock, Kochuhur, ZAFLA…" autofocus>
<button onclick="go()">Искать</button>
<div id=out></div>
<script>
async function go(){
  const r = await fetch('/api/search?q='+encodeURIComponent(document.getElementById('q').value)+'&limit=50');
  const d = await r.json();
  document.getElementById('out').innerHTML = d.results.map(h =>
    `<div class=hit><b>#${h.id} ${h.name}</b> <small>${h.ext}, ${h.size} байт</small><br>${h.snippet}<br>
     <a href='/api/file/${h.id}?text=1'>текст</a> · <a href='/api/file/${h.id}/original'>оригинал</a></div>`).join('')
    || '<p>Ничего не найдено.</p>';
}
document.getElementById('q').addEventListener('keydown', e => { if (e.key==='Enter') go(); });
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    db: AuditsDB = None  # задаётся в main()
    server_version = "ZAFLA-Audits/1.0"

    # ---------------------------------------------------------------- utils
    def _json(self, obj, code: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # тише в консоль: только ошибки
        pass

    # ---------------------------------------------------------------- router
    def do_GET(self) -> None:  # noqa: N802 (имя требует BaseHTTPRequestHandler)
        try:
            self._route()
        except BrokenPipeError:
            pass
        except Exception as exc:  # noqa: BLE001
            self._json({"error": str(exc)}, 500)

    def _route(self) -> None:
        url = urlparse(self.path)
        path = unquote(url.path)
        qs = parse_qs(url.query)
        limit = min(int(qs.get("limit", [20])[0] or 20), 200)
        offset = max(int(qs.get("offset", [0])[0] or 0), 0)
        db = self.db

        if path == "/":
            return self._html(INDEX_HTML)
        if path == "/api/stats":
            return self._json(db.stats())
        if path == "/api/meta":
            return self._json(db.meta())
        if path == "/api/search":
            q = qs.get("q", [""])[0].strip()
            if not q:
                return self._json({"error": "пустой запрос ?q="}, 400)
            return self._json({"query": q, "results": db.search(q, limit, offset)})
        if path == "/api/files":
            ext = qs.get("ext", [None])[0]
            items = list(db.iter_files(ext))[offset:offset + limit]
            return self._json({"results": items, "limit": limit, "offset": offset})
        if path == "/api/signatures":
            return self._json({"results": db.signatures(limit)})
        if path == "/api/certifications":
            return self._json({"results": db.certifications(limit)})

        if path.startswith("/api/file/"):
            rest = path[len("/api/file/"):]
            if rest.endswith("/original"):
                fid = int(rest[: -len("/original")])
                name, data = db.get_original_bytes(fid)
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="file_{fid}{name[name.rfind("."):]}"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            fid = int(rest)
            doc = db.get_file(fid, with_text=qs.get("text", ["0"])[0] == "1")
            if doc is None:
                return self._json({"error": "not found"}, 404)
            return self._json(doc)

        return self._json({"error": "unknown endpoint"}, 404)


def main() -> None:
    ap = argparse.ArgumentParser(description="HTTP API для базы аудитов ZAFLA")
    ap.add_argument("--db", default=DEFAULT_DB_PATH, help="путь к AUDITS_DB.sqlite")
    ap.add_argument("--host", default="127.0.0.1", help="0.0.0.0 — доступ из сети")
    ap.add_argument("--port", type=int, default=8017)
    args = ap.parse_args()

    Handler.db = AuditsDB(args.db)
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"ZAFLA Audits API: http://{args.host}:{args.port}  (Ctrl+C — стоп)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
