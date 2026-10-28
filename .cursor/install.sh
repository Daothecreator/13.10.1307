#!/usr/bin/env bash
# Idempotent bootstrap for the ZAFLA audits API and the bundled ATLAS database.
# Python dependencies are the standard library only. The 1.2 GiB audits
# database is fetched from the public GitHub release and checked with SHA-256.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=zafla-repo.sh
source "$SCRIPT_DIR/zafla-repo.sh"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1 || ! command -v unzip >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends python3 unzip ca-certificates
fi

python3 - <<'PY'
import sqlite3
import sys
if sys.version_info < (3, 9):
    raise SystemExit(f"Python 3.9+ required, found {sys.version}")
sqlite3.connect(":memory:").close()
PY

AUDITS_DIR="$(locate_audits_repo "$ROOT")" || {
  echo "Could not find the 17 audits repository (src/server.py)." >&2
  exit 1
}
echo "Audits repo: $AUDITS_DIR"

export PYTHONPYCACHEPREFIX="${HOME:-/home/ubuntu}/.cache/zafla/pyc"
mkdir -p "$PYTHONPYCACHEPREFIX"

python3 -m py_compile \
  "$AUDITS_DIR/src/server.py" \
  "$AUDITS_DIR/src/audits_db.py" \
  "$AUDITS_DIR/src/download_db.py" \
  "$AUDITS_DIR/examples/quickstart.py" \
  "$AUDITS_DIR/atlas_pipeline.py"

# Default paths used by quickstart.py and server.py. Both filenames are gitignored.
python3 "$AUDITS_DIR/src/download_db.py" "$AUDITS_DIR/AUDITS_DB.sqlite"

if [[ ! -s "$AUDITS_DIR/atlas.db" ]]; then
  unzip -q -o "$AUDITS_DIR/atlas.db.zip" -d "$AUDITS_DIR"
fi

python3 - "$AUDITS_DIR" <<'PY'
import sqlite3
import sys

root = sys.argv[1]
audits = sqlite3.connect(f"{root}/AUDITS_DB.sqlite")
files = audits.execute("SELECT COUNT(*) FROM files").fetchone()[0]
print(f"AUDITS_DB files: {files}")
if files < 1:
    raise SystemExit("AUDITS_DB has no files")
atlas = sqlite3.connect(f"{root}/atlas.db")
events = atlas.execute("SELECT COUNT(*) FROM events").fetchone()[0]
print(f"atlas events: {events}")
if events < 1:
    raise SystemExit("atlas.db has no events")
PY

echo "Install complete."
