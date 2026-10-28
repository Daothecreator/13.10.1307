#!/usr/bin/env bash
# Serve the ZAFLA audits API. Safe to run again: if port 8017 is open, exit 0.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=zafla-repo.sh
source "$SCRIPT_DIR/zafla-repo.sh"
cd "$ROOT"

AUDITS_DIR="$(locate_audits_repo "$ROOT")" || {
  echo "Could not find the 17 audits repository (src/server.py)." >&2
  exit 1
}
CACHE="$(zafla_cache_dir)"
DB="$CACHE/AUDITS_DB.sqlite"
if [[ ! -f "$DB" ]]; then
  echo "Missing $DB. Run .cursor/install.sh first." >&2
  exit 1
fi

if python3 - <<'PY'
import socket
import sys
sock = socket.socket()
sock.settimeout(1)
try:
    sock.connect(("127.0.0.1", 8017))
except OSError:
    sys.exit(1)
finally:
    sock.close()
PY
then
  echo "ZAFLA audits API already listening on port 8017."
  exit 0
fi

cd "$AUDITS_DIR"
exec python3 src/server.py --db "$DB" --host 0.0.0.0 --port 8017
