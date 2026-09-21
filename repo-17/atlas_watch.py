#!/usr/bin/env python3
"""ATLAS watcher: keeps the database alive.
Polls the three roots for new/changed files; on change, re-runs the
deterministic pipeline (scan -> dedup -> curated ingest -> report).
Stdlib only. Stop with Ctrl+C.
"""
import os, sys, time, subprocess, hashlib

ATLAS_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE  = os.path.join(ATLAS_DIR, 'atlas_pipeline.py')
ROOTS     = os.environ.get('ATLAS_ROOTS',
    r'D:\Database;D:\Аудиты;C:\Users\ZAFLA\.copilot\attachments')
POLL_SEC  = int(os.environ.get('ATLAS_POLL_SEC', '300'))   # 5 min default
SKIP_EXT  = {'.zip', '.7z', '.rar', '.gz', '.iso', '.exe', '.dll'}

def fingerprint(roots):
    """Cheap change detector: count + sum of (size,mtime) hashes per root."""
    h = hashlib.sha256()
    for root in roots.split(';'):
        root = root.strip()
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ('.git', 'node_modules')]
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in SKIP_EXT:
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                h.update(f'{p}|{st.st_size}|{st.st_mtime_ns}'.encode('utf-8', 'ignore'))
    return h.hexdigest()

def rebuild():
    print(f'[watch {time.strftime("%H:%M:%S")}] change detected -> rebuilding')
    r = subprocess.run([sys.executable, PIPELINE, '--roots', ROOTS, '--out', ATLAS_DIR],
                       capture_output=True, text=True)
    tail = (r.stdout or '').strip().splitlines()[-1:] or ['(no output)']
    print(f'[watch] rebuild exit={r.returncode} :: {tail[0]}')

def main():
    print(f'[watch] roots: {ROOTS}')
    print(f'[watch] poll every {POLL_SEC}s; Ctrl+C to stop')
    fp = fingerprint(ROOTS)
    print(f'[watch] baseline {fp[:12]}')
    while True:
        time.sleep(POLL_SEC)
        try:
            fp2 = fingerprint(ROOTS)
        except Exception as e:
            print(f'[watch] scan error: {e}')
            continue
        if fp2 != fp:
            fp = fp2
            rebuild()

if __name__ == '__main__':
    main()
