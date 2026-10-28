#!/usr/bin/env bash
# Shared lookup for the ZAFLA audits checkout (repository "17").
# The standalone checkout is preferred. repo-17 inside this repository is the
# fallback when a machine only has 13.10.1307.

locate_audits_repo() {
  local root="${1:-$PWD}"
  local parent candidate found
  parent="$(cd "$(dirname "$root")" && pwd)"
  local candidates=(
    "${AUDITS_REPO:-}"
    "$parent/17"
    "$root/../17"
    "/agent/repos/17"
    "/workspace/17"
    "/workspace/repos/17"
    "$root/repo-17"
  )
  for candidate in "${candidates[@]}"; do
    if [[ -n "$candidate" && -f "$candidate/src/server.py" && -f "$candidate/src/download_db.py" && -f "$candidate/atlas.db.zip" ]]; then
      (cd "$candidate" && pwd)
      return 0
    fi
  done
  found="$(find /agent /workspace /home/ubuntu -maxdepth 5 -type f -path '*/17/src/download_db.py' -print -quit 2>/dev/null || true)"
  if [[ -n "$found" ]]; then
    (cd "$(dirname "$found")/.." && pwd)
    return 0
  fi
  return 1
}

zafla_cache_dir() {
  printf '%s\n' "${ZAFLA_CACHE:-${HOME:-/home/ubuntu}/.cache/zafla}"
}
