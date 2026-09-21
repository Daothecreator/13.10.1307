import os
import csv
import sqlite3
import hashlib
import json
import subprocess
from datetime import datetime, timezone

def get_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS artifacts (id TEXT PRIMARY KEY, type TEXT, checksum TEXT, uri TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS actors (id TEXT PRIMARY KEY, canonical_name TEXT, role TEXT, email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, summary TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS edges (source TEXT, predicate TEXT, target TEXT, evidence_ref TEXT)''')
    conn.commit()
    return conn

def safe_slug(text):
    return text.replace("/", "_").replace(".", "_").replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").replace("<", "").replace(">", "").upper()[:50]

def parse_csv(filepath, c):
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            file_id = f"ART_{safe_slug(filepath)}"

            for row in reader:
                title = row.get('title', '')
                authors_raw = row.get('authors', '')
                year = row.get('year', '')

                if not title and not authors_raw:
                    continue # Skip empty rows

                # We consider every row an Event (e.g. publication/record)
                pub_evt_id = f"EVT_{safe_slug(title + str(year))}"
                c.execute('INSERT OR IGNORE INTO events (id, summary, timestamp) VALUES (?, ?, ?)', (pub_evt_id, f"Record: {title[:30]}", f"{year}-01-01T00:00:00Z" if year else "Unknown"))
                c.execute('INSERT INTO edges (source, predicate, target, evidence_ref) VALUES (?, ?, ?, ?)', (pub_evt_id, "EVIDENCED_BY", file_id, filepath))

                if authors_raw:
                    authors = [a.strip() for a in authors_raw.split(',')]
                    for author in authors:
                        if not author: continue
                        actor_id = f"ACT_{safe_slug(author)}"
                        c.execute('INSERT OR IGNORE INTO actors (id, canonical_name, role, email) VALUES (?, ?, ?, ?)', (actor_id, author, "Entity/Author", ""))
                        c.execute('INSERT INTO edges (source, predicate, target, evidence_ref) VALUES (?, ?, ?, ?)', (actor_id, "AUTHORED_BY", pub_evt_id, filepath))
    except Exception as e:
        print(f"Error parsing CSV {filepath}: {e}")

def process_git_log(c):
    try:
        # Get git log --all --pretty=fuller
        output = subprocess.check_output(['git', 'log', '--all', '--pretty=fuller']).decode('utf-8', errors='ignore')
        current_commit = None
        current_author = None

        for line in output.split('\n'):
            if line.startswith('commit '):
                current_commit = line.split(' ')[1]

                # Add commit as Event
                evt_id = f"EVT_COMMIT_{current_commit[:8]}"
                c.execute('INSERT OR IGNORE INTO events (id, summary, timestamp) VALUES (?, ?, ?)', (evt_id, f"Git Commit {current_commit[:8]}", "Unknown"))

                if current_author:
                    c.execute('INSERT INTO edges (source, predicate, target, evidence_ref) VALUES (?, ?, ?, ?)', (current_author, "INITIATED_BY", evt_id, f"git:{current_commit}"))

            elif line.startswith('Author: '):
                author_info = line[8:].strip()
                # Parse "Name <email>"
                parts = author_info.split('<')
                name = parts[0].strip()
                email = parts[1].replace('>', '').strip() if len(parts) > 1 else ""

                author_id = f"ACT_GIT_{safe_slug(name)}"
                current_author = author_id

                c.execute('INSERT OR IGNORE INTO actors (id, canonical_name, role, email) VALUES (?, ?, ?, ?)', (author_id, name, "Committer", email))

    except Exception as e:
        print(f"Error processing git logs: {e}")

def scan_files(conn):
    c = conn.cursor()
    for root, _, files in os.walk("."):
        if ".git" in root or "meta" in root:
            continue

        for file in files:
            # Skip script outputs and script itself
            if file in ['build_causal_graph.py', 'causal_map.db', 'forensic_whitepaper.md', '.gitignore']:
                continue

            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, ".")

            file_id = f"ART_{safe_slug(rel_path)}"
            checksum = get_sha256(filepath)

            # Identify file type
            ftype = "Document"
            if file.endswith('.csv'): ftype = "Data"
            elif file.endswith(('.py', '.c', '.rs', '.js', '.ts')): ftype = "Code"
            elif file.endswith(('.md', '.txt')): ftype = "Text"
            elif file.endswith('.pdf'): ftype = "PDF"

            c.execute('INSERT OR IGNORE INTO artifacts (id, type, checksum, uri) VALUES (?, ?, ?, ?)', (file_id, ftype, checksum, rel_path))

            if file.endswith('.csv'):
                parse_csv(filepath, c)

    conn.commit()


def generate_outputs(conn):
    c = conn.cursor()
    repo_name = os.path.basename(os.getcwd())
    if not repo_name: repo_name = "unknown_repo"

    last_commit_hash = "Unknown"
    try:
        last_commit_hash = subprocess.check_output(['git', 'log', '-1', '--format=%H']).decode().strip()
    except:
        pass

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    nodes = []
    edges = []

    c.execute("SELECT id, canonical_name, role FROM actors")
    actors = c.fetchall()
    for row in actors:
        nodes.append({"id": row[0], "type": "Actor", "canonical_name": row[1], "role": row[2]})

    c.execute("SELECT id, summary, timestamp FROM events")
    events = c.fetchall()
    for row in events:
        nodes.append({"id": row[0], "type": "Event", "summary": row[1], "timestamp": row[2]})

    c.execute("SELECT id, type, checksum, uri FROM artifacts")
    artifacts = c.fetchall()
    for row in artifacts:
        nodes.append({"id": row[0], "type": "Artifact", "artifact_type": row[1], "checksum": row[2], "uri": row[3]})

    c.execute("SELECT source, predicate, target, evidence_ref FROM edges")
    edges_raw = c.fetchall()
    for row in edges_raw:
        edges.append({"source": row[0], "predicate": row[1], "target": row[2], "evidence_ref": row[3], "timestamp": "Unknown"})

    graph = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "metadata": {
            "repository": repo_name,
            "last_commit": last_commit_hash,
            "generated_at": generated_at,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        },
        "nodes": nodes,
        "edges": edges
    }

    os.makedirs("meta", exist_ok=True)
    with open("meta/CAUSAL_GRAPH.json", "w") as f:
        json.dump(graph, f, indent=2)

    with open("forensic_whitepaper.md", "w") as out:
        out.write("# Forensic Causal Audit Whitepaper\n\n")
        out.write("## 1. Executive Summary\n")
        out.write(f"Repository: {graph['metadata']['repository']}\n")
        out.write(f"Last Commit: {graph['metadata']['last_commit']}\n")
        out.write(f"Generated At: {graph['metadata']['generated_at']}\n")
        out.write(f"Total Nodes: {graph['metadata']['total_nodes']}\n")
        out.write(f"Total Edges: {graph['metadata']['total_edges']}\n\n")

        out.write("## 2. Entities (Actors)\n")
        out.write(f"Total Authors/Entities extracted: {len(actors)}\n\n")
        for actor in actors:
            out.write(f"### {actor[1]}\n")
            out.write(f"- **ID:** {actor[0]}\n")
            out.write(f"- **Role:** {actor[2]}\n\n")

        out.write("## 3. Events (Commits & Records)\n")
        out.write(f"Total Events extracted: {len(events)}\n\n")
        for event in events:
            out.write(f"### {event[1]}\n")
            out.write(f"- **ID:** {event[0]}\n")
            out.write(f"- **Timestamp:** {event[2]}\n\n")

        out.write("## 4. Artifacts (Repository Files)\n")
        out.write(f"Total Artifacts extracted: {len(artifacts)}\n\n")
        for artifact in artifacts:
            out.write(f"### {artifact[3]}\n")
            out.write(f"- **ID:** {artifact[0]}\n")
            out.write(f"- **Type:** {artifact[1]}\n")
            out.write(f"- **Checksum:** {artifact[2]}\n\n")

        out.write("## 5. Causal Chains (Edges)\n")
        out.write(f"Total connections mapped: {len(edges_raw)}\n\n")
        for edge in edges_raw:
            out.write(f"- **{edge[0]}** -> `{edge[1]}` -> **{edge[2]}** (Evidence: {edge[3]})\n")

def main():
    db_path = 'causal_map.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = init_db(db_path)

    # 1. Scan git log
    process_git_log(conn.cursor())

    # 2. Recursively scan all files and parse CSVs
    scan_files(conn)

    # 3. Generate requested outputs
    generate_outputs(conn)

    conn.close()

if __name__ == "__main__":
    main()
