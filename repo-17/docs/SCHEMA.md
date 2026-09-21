# Схема базы данных AUDITS_DB.sqlite

© Davyd Kochuhur (Zero Azimuth Vivifactor), 2026.

SQLite 3, FTS5. Проверка целостности: `PRAGMA integrity_check;` → `ok`.
SHA-256 файла БД: `4570eaec8c720988d82532cc2ec05bf033bd73274e6ef4233a0e8fa5822b67e8`
(см. также `checksums.txt` и `manifest.json`).

## Таблицы

### `meta` — метаданные базы
| Колонка | Тип | Описание |
|---|---|---|
| `key` | TEXT PK | ключ (`author`, `alias`, `created`, `db_sha256`, …) |
| `value` | TEXT | значение |

### `authors` — авторство
| Колонка | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | |
| `name` | TEXT | Davyd Kochuhur / DAVYD KOCHUHUR |
| `alias` | TEXT | Zero Azimuth Vivifactor; Zero Azimuth Full Liability Authority (ZAFLA) |
| `role` | TEXT | `author` |
| `note` | TEXT | комментарий |

### `files` — 1026 документов (по одной строке на файл)
| Колонка | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | |
| `orig_name` | TEXT | исходное имя файла (как было на диске) |
| `name` | TEXT | актуальное имя (после переименования по содержимому) |
| `ext` | TEXT | `.docx` / `.pdf` / `.txt` |
| `size` | INTEGER | размер файла в байтах |
| `sha256` | TEXT | SHA-256 оригинальных байтов |
| `mtime` | TEXT | время модификации |
| `pages` | INTEGER | страниц (для pdf/docx, если определено) |
| `title` | TEXT | заголовок из метаданных документа |
| `meta_creator` | TEXT | автор из метаданных документа |
| `text_len` | INTEGER | длина дословного текста |
| `text_clean_len` | INTEGER | длина читаемой копии |
| `has_text` | INTEGER | 1 — текст извлечён |
| `is_duplicate` | INTEGER | 1 — байтовый дубликат другой записи |
| `duplicate_of` | INTEGER | id канонической записи (у дубликатов) |
| `error` | TEXT | ошибка извлечения (у всех 1026 — NULL) |
| `text` | TEXT | **дословный извлечённый текст** (verbatim, без изменений) |
| `text_clean` | TEXT | читаемая копия (схлопнута только XML-разметка Word) |
| `blob` | BLOB | **оригинальные байты файла**; у дубликатов NULL |

Индексы: `idx_files_ext(ext)`, `idx_files_sha(sha256)`, `idx_files_title(title)`.

### `files_fts` — полнотекстовый поиск (FTS5)
Виртуальная таблица `fts5(title, text_clean)`, `rowid = files.id`.

```sql
SELECT f.name, snippet(files_fts, 1, '«', '»', ' … ', 24)
FROM files_fts JOIN files f ON f.id = files_fts.rowid
WHERE files_fts MATCH 'BlackRock'
ORDER BY rank LIMIT 20;
```

### `signatures` — 781 вхождение подписей/имён автора
| Колонка | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | |
| `file_id` | INTEGER → files(id) | документ |
| `kind` | TEXT | вид совпадения (`author_name`, `alias`, `org` …) |
| `match` | TEXT | найденная строка (например `Davyd Kochuhur`) |
| `context` | TEXT | фрагмент контекста |

### `certifications` — 111 идентификаторов
| Колонка | Тип | Описание |
|---|---|---|
| `id` | INTEGER PK | |
| `file_id` | INTEGER → files(id) | документ |
| `kind` | TEXT | вид (`zafla_document_id`, `protocol`, …) |
| `number` | TEXT | значение (`ZAFLA-EXTRACT-RU-2026-0622-Ω`, `BiCA a8f3c9d2e1b40571`, …) |
| `context` | TEXT | фрагмент контекста |

## Дедупликация
952 уникальных SHA-256; 74 записи-дубликата хранят `blob = NULL` и ссылаются
`duplicate_of` на каноническую запись. Функция `AuditsDB.get_original_bytes()`
резолвит это автоматически.
