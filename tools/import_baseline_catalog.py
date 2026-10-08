import argparse, sqlite3, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
try: import yaml
except ImportError: print("ERROR: PyYAML is required.", file=sys.stderr); sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog")
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    with open(args.catalog, "r", encoding="utf-8") as f: data = yaml.safe_load(f)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    from ot_agent.baseline_db import init_baseline_schema
    init_baseline_schema(conn)

    types = data.get("document_types", [])
    for t in types:
        conn.execute('''
            INSERT INTO document_types (type_id, code, title, topic)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(type_id) DO UPDATE SET code=excluded.code, title=excluded.title, updated_at=datetime('now')
        ''', (t["type_id"], t["code"], t["title"], t.get("topic", "OT")))

    docs = data.get("baseline_documents", [])
    for d in docs:
        type_id = next((t["type_id"] for t in types if t["code"] == d["type_code"]), None)
        if not type_id: continue
        conn.execute('''
            INSERT INTO baseline_documents 
            (document_id, type_id, code, title, topic, category, lifecycle_stage, applicability_note, legal_basis_note, template_id, status, verification_status, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET 
            status=excluded.status, verification_status=excluded.verification_status, updated_at=datetime('now')
        ''', (
            d["document_id"], type_id, d["code"], d["title"], d.get("topic", "OT"),
            d.get("category"), d.get("lifecycle_stage"), d.get("applicability_note"),
            d.get("legal_basis_note"), d.get("template_id"), d.get("status", "SUGGESTED"),
            d.get("verification_status", "REQUIRES_VERIFICATION"), d.get("sort_order", 100)
        ))

    total_t = conn.execute("SELECT COUNT(*) FROM document_types").fetchone()[0]
    total_d = conn.execute("SELECT COUNT(*) FROM baseline_documents").fetchone()[0]

    if args.commit:
        conn.commit()
        print(f"COMMIT: YES | types: {total_t} | docs: {total_d}")
    else:
        conn.rollback()
        print(f"COMMIT: NO (dry-run) | types: {total_t} | docs: {total_d}")
    conn.close()

if __name__ == "__main__": main()