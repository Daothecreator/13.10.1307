# How to share ATLAS — three paths, simplest first

Everything here is static files. No server code, no accounts to hack, nothing to defend.
The database (`atlas.db`, ~143 MB, **22.9 MB zipped**) is the **full registry** —
250,053 documents across all three roots, nothing filtered out, nothing skipped.
What the DB contains is *metadata*: paths, hashes, classes, events, verification log.
Source-file **contents** never leave your machine — there is no private third-party
personal data inside the database itself.

---

## Option A — GitHub (download + browse), 10 minutes

1. Create a public repo (any name — e.g. `atlas-knowledge-base`).
2. Put in it: `atlas.db.zip`, `ATLAS_MANIFEST.md`, `README.md`, `schema.sql`,
   `atlas_pipeline.py`, `metadata.json`.
3. The zip is ~23 MB — comfortably under GitHub's 100 MB file limit. No Releases needed.
4. Anyone can now download the DB and open it with any SQLite tool
   (DB Browser for SQLite is free, no install skill needed).

Give Copilot the repo URL and it will do steps 1–4 for you, including commits.

## Option B — Datasette: a real searchable website, ~15 minutes

[Datasette](https://datasette.io/) turns any SQLite file into a browsable,
filterable, SQL-queryable site.

```bash
pip install datasette
datasette atlas.db -m metadata.json --cors
```

Open http://localhost:8001 — every table is explorable, every query shareable as a link.

To put it on the public internet free:
- **Render / Fly.io / Railway** free tier: `datasette publish` or a 3-line Dockerfile.
- Or expose your own machine via **Tailscale Funnel** / **Cloudflare Tunnel** —
  no hosting bill, DB never leaves your computer.

## Option C — Fully static, GitHub Pages, zero backend

[sql.js-httpvfs](https://github.com/phiresky/sql.js-httpvfs) serves SQLite from plain
static hosting with HTTP range requests — visitors run SQL in their browser,
you pay nothing and run nothing. Best long-term fit for "everyone can just walk in
and read"; setup ≈ 30–60 min following the project's README.

---

## The contract for readers (already in the manifest)

- `events` — only public-record anchors (court / official / corporate / published reporting)
- `pending_claims` — assertions still waiting for a source; a queue, not a verdict
- `verifications` — what was checked against primary sources, where, when, result
- Operator-authored material is attributed as such. Nothing is anonymous, nothing is hidden.
