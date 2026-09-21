"""Примеры работы с базой аудитов ZAFLA. Запуск: python examples/quickstart.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from audits_db import AuditsDB  # noqa: E402

with AuditsDB() as db:
    print("== Статистика ==")
    for k, v in db.stats().items():
        print(f"  {k}: {v}")

    print("\n== Поиск: 'BlackRock' (первые 5) ==")
    for hit in db.search("BlackRock", limit=5):
        print(f"  #{hit['id']} {hit['name']}\n    {hit['snippet']}")

    print("\n== Поиск: 'Kochuhur' (первые 5) ==")
    for hit in db.search("Kochuhur", limit=5):
        print(f"  #{hit['id']} {hit['name']}")

    print("\n== Сертификационные идентификаторы автора (первые 10) ==")
    for row in db.certifications(10):
        print(f"  [{row['kind']}] {row['value']}  ← {row['name']}")

    print("\n== Извлечение оригинала документа #1 ==")
    path = db.save_original(1, out_dir=os.path.dirname(__file__))
    print("  сохранено:", path)
