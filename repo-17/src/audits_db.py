"""audits_db — клиентская библиотека для базы аудитов ZAFLA (AUDITS_DB.sqlite).

Автор: Davyd Kochuhur (Zero Azimuth Vivifactor)

База содержит 1026 документа: оригинальные байты, дословный текст,
читаемую копию текста, метаданные и полнотекстовый FTS5-индекс.
Зависимостей нет — только стандартная библиотека Python 3.9+.
"""
from __future__ import annotations

import os
import sqlite3
from typing import Iterator, Optional

DEFAULT_DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDITS_DB.sqlite")
)


def _escape_fts(query: str) -> str:
    """Минимальная санитизация FTS5-запроса: экранируем кавычки."""
    return query.replace('"', '""')


class AuditsDB:
    """Тонкая обёртка над SQLite-базой аудитов."""

    def __init__(self, path: str = DEFAULT_DB_PATH):
        if not os.path.isfile(path):
            raise FileNotFoundError(
                f"База не найдена: {path}\n"
                "Скачайте её: python src/download_db.py"
            )
        self.path = path
        self._con = sqlite3.connect(path, check_same_thread=False)
        self._con.row_factory = sqlite3.Row

    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> "AuditsDB":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ------------------------------------------------------------------ meta
    def meta(self) -> dict:
        return {r["key"]: r["value"] for r in self._con.execute("SELECT key, value FROM meta")}

    def stats(self) -> dict:
        c = self._con
        return {
            "files": c.execute("SELECT COUNT(*) FROM files").fetchone()[0],
            "duplicates": c.execute("SELECT COUNT(*) FROM files WHERE is_duplicate=1").fetchone()[0],
            "unique_blobs": c.execute("SELECT COUNT(*) FROM files WHERE blob IS NOT NULL").fetchone()[0],
            "signatures": c.execute("SELECT COUNT(*) FROM signatures").fetchone()[0],
            "certifications": c.execute("SELECT COUNT(*) FROM certifications").fetchone()[0],
            "by_ext": {r[0]: r[1] for r in c.execute(
                "SELECT ext, COUNT(*) FROM files GROUP BY ext ORDER BY 2 DESC")},
        }

    # --------------------------------------------------------------- search
    def search(self, query: str, limit: int = 20, offset: int = 0) -> list[dict]:
        """Полнотекстовый поиск (FTS5) по названию и тексту документов."""
        sql = """
            SELECT f.id, f.name, f.ext, f.size,
                   snippet(files_fts, 1, '«', '»', ' … ', 24) AS snippet
            FROM files_fts JOIN files f ON f.id = files_fts.rowid
            WHERE files_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        rows = self._con.execute(sql, (_escape_fts(query), limit, offset)).fetchall()
        return [dict(r) for r in rows]

    # ---------------------------------------------------------------- files
    def get_file(self, file_id: int, with_text: bool = False) -> Optional[dict]:
        row = self._con.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
        if row is None:
            return None
        d = dict(row)
        d.pop("blob", None)
        if not with_text:
            d.pop("text", None)
            d.pop("text_clean", None)
        return d

    def iter_files(self, ext: Optional[str] = None) -> Iterator[dict]:
        sql = "SELECT id, name, orig_name, ext, size, sha256, is_duplicate FROM files"
        args: tuple = ()
        if ext:
            sql += " WHERE ext=?"
            args = (ext,)
        sql += " ORDER BY name"
        for r in self._con.execute(sql, args):
            yield dict(r)

    def get_original_bytes(self, file_id: int) -> tuple[str, bytes]:
        """Возвращает (имя, байты) оригинала; дубликаты резолвятся на каноническую копию."""
        row = self._con.execute(
            "SELECT name, blob, duplicate_of FROM files WHERE id=?", (file_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"file id {file_id} not found")
        name, blob, dup = row
        if blob is None and dup is not None:
            blob = self._con.execute("SELECT blob FROM files WHERE id=?", (dup,)).fetchone()[0]
        if blob is None:
            raise ValueError(f"no blob stored for file id {file_id}")
        return name, blob

    def save_original(self, file_id: int, out_dir: str = ".") -> str:
        name, data = self.get_original_bytes(file_id)
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, name)
        with open(out, "wb") as fh:
            fh.write(data)
        return out

    # --------------------------------------------------------- authorship
    def signatures(self, limit: int = 500) -> list[dict]:
        rows = self._con.execute(
            "SELECT s.file_id, f.name, s.kind, s.match AS value FROM signatures s "
            "JOIN files f ON f.id = s.file_id ORDER BY s.kind, value LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def certifications(self, limit: int = 500) -> list[dict]:
        rows = self._con.execute(
            "SELECT c.file_id, f.name, c.kind, c.number AS value FROM certifications c "
            "JOIN files f ON f.id = c.file_id ORDER BY c.kind, value LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


if __name__ == "__main__":
    import json, sys
    with AuditsDB(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH) as db:
        print(json.dumps(db.stats(), ensure_ascii=False, indent=2))
