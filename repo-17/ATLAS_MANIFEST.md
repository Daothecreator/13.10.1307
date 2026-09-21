# ATLAS — Verified World-State Knowledge Base (Machine-Readable Manifest)

**Version:** 1.0 | **Format:** SQLite 3 (`atlas.db`) | **Builder:** `atlas_pipeline.py` (Python 3.10+, stdlib only)
**Determinism:** identical inputs → byte-identical schema content. No network calls. No self-modification. No external services.

## What this is

ATLAS is a **curated relational knowledge base** built from a 34,000-file mixed corpus
(dossiers, audits, datasets, policies, network telemetry, doctrine papers). It separates
**verified public-record fact** from **speculation, fabrication, and private material** at
ingestion time — every record carries its epistemic status. It is not a scraping bot, not
an autonomous agent, and it does not contact other systems. It is a queryable, auditable,
rebuildable data artifact plus the deterministic engine that produces it.

## Layer model

| Layer | Content | Trust rule |
|---|---|---|
| `events` | Dated, real-world events | Only public-record anchors: court rulings, official sanctions, government/regulatory actions, documented corporate actions, major published journalism |
| `entities` + `event_entities` | Persons/orgs/locations/instruments linked to events | Derived only from `events` |
| `documents` | Full corpus registry (path, hash, kind, domain, provenance class) | Every file registered; exclusions flagged, not hidden |
| `pending_claims` | Claims awaiting source location | A sourcing queue, not a verdict — open for anyone to supply a source |
| `verifications` | Claims checked against primary sources | Records what was checked, against which source, when, and the result |
| `exclusions` | Files withheld from ingestion | restricted-personal, media/app binary, duplicates |

## Confidence vocabulary (events.confidence)

`Court-documented` · `Officially designated` · `Official record` · `Published reporting` · `Corporate record`

Anything not meeting these bars is **not in `events`** — it waits in `pending_claims` until a source is located.

## Registry policy (enforced by the pipeline)

**Nothing is deleted and nothing is judged.** Every scanned file is registered with hash,
kind, domain, and a descriptive provenance class — what the document *is*, not whether it
is *true*. Operator-authored content carries its author's attribution
(`operator-authored`: asserted by operator, who takes responsibility for it).

1. Operator-authored doctrine (ZAFLA/AIHS/isomorphic-substrate works) is ingested and
   tagged `operator-authored` — present and queryable as authored material.
2. Material concerning named private third parties is classed `restricted-personal`:
   cataloged in `documents`/`exclusions` but not compiled into the entity/event layer —
   the base never answers "who should be acted against".
3. Claims without a located source live in `pending_claims` — a queue, not a dismissal.
   When a source is found, the claim moves to `events` and the check is logged in
   `verifications` (claim, primary source, result, date).
4. Media/app binaries and exact byte-duplicates are registered without content ingestion.

## Schema (abridged)

```
documents(id, path, source_root, sha256, size_bytes, ext, kind, domain, veracity,
          excluded, is_duplicate, canonical_of, title, mtime)
events(id, date, actors, action, mechanism, outcome, record_type, confidence, source_file, section)
entities(id, name, type)            -- person | organization | location | system | legal-instrument
event_entities(event_id, entity_id, role)
exclusions(id, path, reason)
pending_claims(id, claim, source_file)
verifications(id, claim, source_name, source_url, result, checked_at)
build_log(id, stage, detail, logged_at)
```

## Example queries

```sql
-- Timeline of court-documented events
SELECT date, actors, action FROM events WHERE confidence='Court-documented' ORDER BY date;

-- Everything known about one entity
SELECT e.date, e.action, e.confidence, e.source_file
FROM events e JOIN event_entities ee ON ee.event_id=e.id
JOIN entities en ON en.id=ee.entity_id
WHERE en.name LIKE '%Epstein%' ORDER BY e.date;

-- Claims awaiting a source
SELECT claim, source_file FROM pending_claims;

-- What has been checked against primary sources
SELECT claim, source_name, result, checked_at FROM verifications;
```

## Rebuild / extend

```powershell
python atlas_pipeline.py --roots "D:\Database;D:\Аудиты;C:\...\attachments" --out .
```
To extend: drop new source files into a scanned root, or add curated `extract_*.md`
(`EVENT | date | actors | action | mechanism | outcome | record_type | source_file | section`)
lines, then rerun. The build is idempotent.

## Provenance

Curated extraction files (`extract_*.md`) are the auditable intermediate layer between raw
corpus and database: every event row cites its source file and section. Numbers in
`build_report.json` are regenerated on every build.
