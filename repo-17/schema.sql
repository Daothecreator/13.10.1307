-- ATLAS Knowledge Base Schema v1.0
-- Deterministic rebuild: atlas_pipeline.py regenerates this database from source corpora.

PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS documents (
    id            INTEGER PRIMARY KEY,
    path          TEXT NOT NULL,
    source_root   TEXT NOT NULL,          -- 'Database' | 'Audity' | 'Attachments'
    sha256        TEXT,                   -- NULL for oversized/binary-skipped
    size_bytes    INTEGER,
    ext           TEXT,
    kind          TEXT,                   -- dossier|dataset|script|certificate|charter|report|code|binary|media|other
    domain        TEXT,                   -- finance|military|cyber|legal|energy|telecom|crime|doctrine|scientific|network|policy|personal|general
    veracity      TEXT,                   -- public-record|technical-factual|policy-template|operator-doctrine|mixed|speculative|fabricated|unscored
    excluded      INTEGER DEFAULT 0,      -- 1 = registered but content NOT ingested (see exclusions)
    is_duplicate  INTEGER DEFAULT 0,      -- 1 = exact byte-copy of another document
    canonical_of  TEXT,                   -- sha256 of the kept canonical copy when is_duplicate=1
    title         TEXT,                   -- best-effort internal title
    mtime         TEXT,
    UNIQUE(path, source_root)
);

CREATE INDEX IF NOT EXISTS idx_documents_sha256  ON documents(sha256);
CREATE INDEX IF NOT EXISTS idx_documents_kind    ON documents(kind);
CREATE INDEX IF NOT EXISTS idx_documents_domain  ON documents(domain);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY,
    date        TEXT NOT NULL,            -- YYYY | YYYY-MM | YYYY-MM-DD | range
    actors      TEXT NOT NULL,            -- semicolon-separated
    action      TEXT NOT NULL,
    mechanism   TEXT,
    outcome     TEXT,
    record_type TEXT NOT NULL,            -- court ruling|sanctions|official report|journalism|corporate action
    confidence  TEXT NOT NULL,            -- Court-documented|Officially designated|Official record|Published reporting|Corporate record
    source_file TEXT NOT NULL,
    section     TEXT,
    UNIQUE(date, actors, action)
);

CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);

CREATE TABLE IF NOT EXISTS entities (
    id   INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL                    -- person|organization|location|system|legal-instrument
);

CREATE TABLE IF NOT EXISTS event_entities (
    event_id  INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    role      TEXT DEFAULT 'participant',
    UNIQUE(event_id, entity_id)
);

CREATE TABLE IF NOT EXISTS exclusions (
    id     INTEGER PRIMARY KEY,
    path   TEXT NOT NULL,
    reason TEXT NOT NULL                  -- operator-personal|targeting|media-binary|app-binary|duplicate|unsafe-content
);

CREATE TABLE IF NOT EXISTS pending_claims (
    id          INTEGER PRIMARY KEY,
    claim       TEXT NOT NULL,            -- assertion awaiting a located source (queue, not verdict)
    source_file TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verifications (
    id          INTEGER PRIMARY KEY,
    claim       TEXT NOT NULL,
    source_name TEXT,
    source_url  TEXT,
    result      TEXT,                     -- confirmed | confirmed-secondary | no-record-located
    checked_at  TEXT
);

CREATE TABLE IF NOT EXISTS build_log (
    id         INTEGER PRIMARY KEY,
    stage      TEXT NOT NULL,
    detail     TEXT,
    logged_at  TEXT DEFAULT (datetime('now'))
);
