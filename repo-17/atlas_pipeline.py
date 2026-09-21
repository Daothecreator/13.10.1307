#!/usr/bin/env python3
"""
ATLAS Pipeline v1.0 - deterministic knowledge-base builder.

Rebuilds atlas.db from source corpora with zero network access, zero
self-modification, and a full audit trail. "Auto-execution" here means:
run the script, get an identical, verifiable database every time.

Stages: scan -> dedup -> classify -> ingest-curated -> build -> report

Usage:
    python atlas_pipeline.py --roots "D:\\Database;D:\\Audity;C:\\...\\attachments" --out .
    python atlas_pipeline.py --inventory inv_database.csv inv_audity.csv   (fast rescan)
"""
import argparse, csv, hashlib, json, os, re, sqlite3, sys
from pathlib import Path

MEDIA_EXT = {'.png','.jpg','.jpeg','.gif','.webp','.svg','.ico','.mp3','.mp4','.wav',
             '.avi','.mov','.mkv','.flac','.ogg','.stl','.woff','.woff2','.ttf','.eot'}
APP_EXT   = {'.apk','.exe','.dll','.so','.dylib','.jar','.msi','.packlist','.map'}
TEXT_EXT  = {'.md','.txt','.csv','.json','.html','.htm','.tsv','.xml','.yaml','.yml','.log'}
CODE_EXT  = {'.py','.js','.ts','.tsx','.c','.h','.cpp','.pl','.pm','.pod','.bat','.ps1','.sh','.go','.rs'}
DOC_EXT   = {'.pdf','.docx','.doc','.rtf','.odt'}
CERT_EXT  = {'.pem','.crt','.cer','.key','.der','.p12','.pfx'}

OPERATOR_PERSONAL = ['kochuhur', 'zero azimuth', 'zero_azimuth', 'room811', 'davyd']
TARGETING_HINTS   = ['human_targets_action_protocol', 'exposed_personnel', 'threat_matrix',
                     'action_vectors', 'witt_']
MIXED_VERACITY_FILES = ['cluster-', 'global_governance_architecture_2026', 'integrated_report_global',
                        'criminal_event_map', 'historical_chronology', 'san-francisco-37n',
                        'sonoma-ca-38n', 'ontology_causal_chain']

DOMAIN_RULES = [
    ('finance',   r'swift|blackrock|vanguard|dtcc|\bbis\b|fincen|offshore|panama|pandora|bank|financ'),
    ('military',  r'norad|stratcom|pentagon|nato|defen[cs]e|missile|weapon'),
    ('cyber',     r'apt\d+|ransomware|malware|xkeyscore|prism|surveillance|cyber'),
    ('network',   r'as\d{4,5}|bgp|looking.?glass|cable|datacenter|equinix|icann'),
    ('legal',     r'indict|court|settlement|sanction|treaty|affidavit|legal|judicial|charter'),
    ('energy',    r'oil|gas|ghawar|hormuz|suez|panama canal|energy'),
    ('crime',     r'cartel|traffic|launder|crime|criminal|epstein|murd?er'),
    ('doctrine',  r'zafla|bica|sovereign|charter|ontolog|masonic|fraternal'),
    ('scientific',r'collider|neutron|transmut|murashu|particle|quantum'),
    ('policy',    r'anti.?bribery|anti.?slavery|policy|compliance'),
    ('personal',  r'legal_consultation|stas_legal|income_now|grant'),
]
CONFIDENCE = {
    'court ruling': 'Court-documented', 'sanctions': 'Officially designated',
    'official report': 'Official record', 'journalism': 'Published reporting',
    'corporate action': 'Corporate record',
    # extended record types from dataset extraction
    'court-case': 'Court-documented', 'judicial': 'Court-documented',
    'journalism/court': 'Court-documented',
    'regulatory': 'Officially designated', 'regulatory-action': 'Officially designated',
    'government action': 'Officially designated', 'government-disclosure': 'Official record',
    'declassified-report': 'Official record', 'leaked-doc': 'Published reporting',
    'leaked-doc/reporting': 'Published reporting',
    'journalism/regulatory': 'Published reporting',
    'documented-event': 'Official record', 'public-record': 'Official record',
    'historical-archive': 'Official record', 'historical-contract': 'Official record',
    'historical-record': 'Official record', 'archaeology': 'Official record',
    'academic-paper': 'Official record', 'technical-report': 'Official record',
    'industry-report': 'Official record', 'threat-intel-IOCs': 'Published reporting',
    'corporate-action': 'Corporate record',
}

def sha256_of(path, limit=200*1024*1024):
    if os.path.getsize(path) > limit:
        return None
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def classify_kind(ext):
    if ext in MEDIA_EXT: return 'media'
    if ext in APP_EXT:   return 'binary'
    if ext in TEXT_EXT:  return 'dataset' if ext in ('.csv', '.tsv', '.json') else 'dossier'
    if ext in CODE_EXT:  return 'script'
    if ext in CERT_EXT:  return 'certificate'
    if ext in DOC_EXT:   return 'report'
    if ext in ('.zip', '.7z', '.rar', '.tar', '.gz'): return 'archive'
    return 'other'

def classify_domain(name_path):
    low = name_path.lower()
    for dom, pat in DOMAIN_RULES:
        if re.search(pat, low):
            return dom
    return 'general'

def extract_title(path, ext):
    if ext not in ('.md', '.txt', '.html', '.htm'):
        return None
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in range(60):
                line = f.readline()
                if not line:
                    break
                s = line.strip().lstrip('#').strip()
                if len(s) > 8 and not s.startswith('<'):
                    return s[:200]
    except OSError:
        pass
    return None

def scan(roots, conn):
    cur = conn.cursor()
    n = 0
    for root in roots:
        root = Path(root)
        if not root.exists():
            print(f'  [skip] missing root: {root}')
            continue
        label = ('Attachments' if 'attachments' in root.name.lower()
                 else 'Audity' if 'удиты' in root.name.lower() else 'Database')
        for p in root.rglob('*'):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            kind = classify_kind(ext)
            low = str(p).lower()
            base = p.name.lower()
            excluded, reason = 0, None
            veracity = 'unscored'
            domain = classify_domain(str(p))
            if any(t in low for t in OPERATOR_PERSONAL):
                domain, veracity = 'personal', 'operator-authored'
            elif any(t in low for t in TARGETING_HINTS):
                excluded, reason = 1, 'targeting'
                veracity = 'restricted-personal'
            elif kind == 'media':
                excluded, reason = 1, 'media-binary'
            elif kind == 'binary':
                excluded, reason = 1, 'app-binary'
            elif any(t in base for t in MIXED_VERACITY_FILES):
                veracity = 'compilation'
            elif domain == 'doctrine':
                veracity = 'operator-authored'
            cur.execute('''INSERT OR IGNORE INTO documents
                (path, source_root, size_bytes, ext, kind, domain, veracity, excluded, mtime)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (str(p), label, p.stat().st_size, ext, kind,
                 domain, veracity, excluded,
                 str(int(p.stat().st_mtime))))
            if excluded:
                cur.execute('INSERT OR IGNORE INTO exclusions (path, reason) VALUES (?,?)',
                            (str(p), reason))
            n += 1
    conn.commit()
    cur.execute("INSERT INTO build_log (stage, detail) VALUES ('scan', ?)", (f'{n} files',))
    conn.commit()
    return n

def dedup(conn):
    cur = conn.cursor()
    rows = cur.execute('''SELECT id, path, size_bytes FROM documents
                          WHERE excluded = 0 AND is_duplicate = 0''').fetchall()
    by_size = {}
    for rid, path, size in rows:
        by_size.setdefault(size, []).append((rid, path))
    hashed = dup = 0
    for size, group in by_size.items():
        if len(group) < 2:
            continue
        by_hash = {}
        for rid, path in group:
            try:
                h = sha256_of(path)
            except OSError:
                continue
            if h is None:
                continue
            hashed += 1
            by_hash.setdefault(h, []).append((rid, path))
        for h, copies in by_hash.items():
            if len(copies) < 2:
                continue
            copies.sort(key=lambda c: (('copy' in c[1].lower()) + len(c[1]), c[1]))
            for rid, path in copies[1:]:
                cur.execute('UPDATE documents SET is_duplicate=1, canonical_of=?, sha256=? WHERE id=?',
                            (h, h, rid))
                cur.execute('INSERT OR IGNORE INTO exclusions (path, reason) VALUES (?,?)',
                            (path, 'duplicate'))
                dup += 1
            cur.execute('UPDATE documents SET sha256=? WHERE id=?', (h, copies[0][0]))
    conn.commit()
    cur.execute("INSERT INTO build_log (stage, detail) VALUES ('dedup', ?)",
                (f'{hashed} hashed, {dup} duplicates',))
    conn.commit()
    return hashed, dup

def parse_event_line(line):
    parts = [p.strip() for p in line.split('|')]
    if len(parts) < 9 or parts[0] != 'EVENT':
        return None
    return dict(zip(['tag','date','actors','action','mechanism','outcome',
                     'record_type','source_file','section'], parts))

def entity_type(name):
    low = name.lower()
    if any(w in low for w in ('court','senate','congress','parliament','icj','scotus')):
        return 'legal-instrument'
    if any(w in low for w in ('bank','corp','inc','llc','ltd','group','agency','bureau',
                              'commission','ministry','department','fed','nsa','cia','fbi',
                              'nato','un','eu','icij','guardian','wikileaks')):
        return 'organization'
    if re.match(r'^[A-Z][a-z]+( [A-Z][a-z]+)+$', name) and len(name.split()) <= 4:
        return 'person'
    return 'organization'

def ingest_extracts(conn, curated_dir):
    cur = conn.cursor()
    nev = ncau = 0
    for f in sorted(Path(curated_dir).glob('extract_*.md')):
        for line in f.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            ev = parse_event_line(line)
            if ev:
                rt = re.sub(r'\s*\(.*\)$', '', ev['record_type']).strip()
                conf = CONFIDENCE.get(rt, 'Official record')
                cur.execute('''INSERT OR IGNORE INTO events
                    (date, actors, action, mechanism, outcome, record_type, confidence, source_file, section)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                    (ev['date'], ev['actors'], ev['action'], ev['mechanism'], ev['outcome'],
                     rt, conf, ev['source_file'], ev['section']))
                if cur.rowcount:
                    nev += 1
                    eid = cur.execute('SELECT id FROM events WHERE date=? AND actors=? AND action=?',
                                      (ev['date'], ev['actors'], ev['action'])).fetchone()[0]
                    for name in re.split(r'\s*/\s*|\s*;\s*', ev['actors']):
                        name = name.strip(' .')
                        if not name or len(name) < 3:
                            continue
                        cur.execute('INSERT OR IGNORE INTO entities (name, type) VALUES (?,?)',
                                    (name, entity_type(name)))
                        ent = cur.execute('SELECT id FROM entities WHERE name=?', (name,)).fetchone()[0]
                        cur.execute('INSERT OR IGNORE INTO event_entities (event_id, entity_id) VALUES (?,?)',
                                    (eid, ent))
            elif line.startswith('CAUTION |') or (line[:2].isdigit() and '. ' in line[:5]):
                text = line
                if line.startswith('CAUTION |'):
                    text = line[len('CAUTION |'):].strip()
                else:
                    text = line.lstrip('-0123456789. ').strip()
                if len(text) > 25:
                    src = f.name
                    if '|' in text:
                        text, src = [x.strip() for x in text.rsplit('|', 1)]
                    cur.execute('INSERT INTO pending_claims (claim, source_file) VALUES (?,?)', (text, src))
                    ncau += 1
    conn.commit()
    cur.execute("INSERT INTO build_log (stage, detail) VALUES ('curated', ?)",
                (f'{nev} events, {ncau} pending_claims',))
    conn.commit()
    return nev, ncau

def ingest_classifications(conn, curated_dir):
    """Apply agent DOC-block classifications to matching document rows by filename."""
    cur = conn.cursor()
    applied = 0
    for f in sorted(Path(curated_dir).glob('extract_attachments_*.md')):
        text = f.read_text(encoding='utf-8', errors='ignore')
        for block in re.split(r'\n(?=DOC \| )', text):
            m = {k: v.strip() for k, v in
                 re.findall(r'^(DOC|TITLE|VERACITY|EXCLUDE) \| (.+)$', block, re.M)}
            if 'DOC' not in m:
                continue
            veracity = m.get('VERACITY', 'unscored')
            title = m.get('TITLE')
            excl = m.get('EXCLUDE', 'none')
            stem = m['DOC'].lower().replace('.pdf', '').replace('...', '')
            stem = re.sub(r'[^a-z0-9а-я]+', '%', stem)
            rows = cur.execute(
                "SELECT id, path FROM documents WHERE source_root='Attachments' AND lower(path) LIKE ?",
                (f'%{stem}%',)).fetchall()
            for rid, path in rows:
                cur.execute('UPDATE documents SET veracity=?, title=COALESCE(?, title) WHERE id=?',
                            (veracity, title, rid))
                if 'targeting' in excl:
                    cur.execute('UPDATE documents SET excluded=1 WHERE id=?', (rid,))
                    cur.execute('INSERT OR IGNORE INTO exclusions (path, reason) VALUES (?,?)',
                                (path, 'targeting'))
                applied += 1
    conn.commit()
    cur.execute("INSERT INTO build_log (stage, detail) VALUES ('classifications', ?)",
                (f'{applied} applied',))
    conn.commit()
    return applied

def report(conn, out_dir):
    cur = conn.cursor()
    stats = {
        'documents_total':    cur.execute('SELECT COUNT(*) FROM documents').fetchone()[0],
        'documents_excluded': cur.execute('SELECT COUNT(*) FROM documents WHERE excluded=1').fetchone()[0],
        'duplicates':         cur.execute('SELECT COUNT(*) FROM documents WHERE is_duplicate=1').fetchone()[0],
        'by_kind':  dict(cur.execute('SELECT kind, COUNT(*) FROM documents GROUP BY kind')),
        'by_domain':dict(cur.execute('SELECT domain, COUNT(*) FROM documents GROUP BY domain')),
        'events':   cur.execute('SELECT COUNT(*) FROM events').fetchone()[0],
        'entities': cur.execute('SELECT COUNT(*) FROM entities').fetchone()[0],
        'links':    cur.execute('SELECT COUNT(*) FROM event_entities').fetchone()[0],
        'pending_claims': cur.execute('SELECT COUNT(*) FROM pending_claims').fetchone()[0],
    }
    (Path(out_dir) / 'build_report.json').write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return stats

def main():
    ap = argparse.ArgumentParser(description='ATLAS deterministic knowledge-base builder')
    ap.add_argument('--roots', default='',
                    help='Semicolon-separated source roots to scan (live filesystem)')
    ap.add_argument('--out', default=str(Path(__file__).parent))
    ap.add_argument('--skip-scan', action='store_true', help='Reuse existing documents table')
    args = ap.parse_args()
    out = Path(args.out)
    db_path = out / 'atlas.db'
    if db_path.exists() and not args.skip_scan:
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.executescript((Path(__file__).parent / 'schema.sql').read_text(encoding='utf-8'))
    if args.roots and not args.skip_scan:
        n = scan(args.roots.split(';'), conn)
        print(f'[scan] {n} files registered')
    h, d = dedup(conn)
    print(f'[dedup] {h} hashed, {d} duplicates')
    nev, ncau = ingest_extracts(conn, Path(__file__).parent.parent)
    print(f'[curated] {nev} events, {ncau} pending_claims')
    nap = ingest_classifications(conn, Path(__file__).parent.parent)
    print(f'[classifications] {nap} applied')
    report(conn, out)
    conn.close()
    print(f'[done] {db_path}')

if __name__ == '__main__':
    main()
