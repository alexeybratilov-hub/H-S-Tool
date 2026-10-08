import sqlite3
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

BASELINE_SCHEMA = '''
CREATE TABLE IF NOT EXISTS document_types (
    type_id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (topic, code)
);

CREATE TABLE IF NOT EXISTS baseline_documents (
    document_id TEXT PRIMARY KEY,
    type_id TEXT NOT NULL REFERENCES document_types(type_id),
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    category TEXT,
    lifecycle_stage TEXT,
    applicability_note TEXT,
    legal_basis_note TEXT,
    template_id TEXT,
    status TEXT NOT NULL DEFAULT 'SUGGESTED'
        CHECK (status IN ('SUGGESTED','USER_CONFIRMED','USER_REJECTED','REQUIRES_VERIFICATION')),
    verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
        CHECK (verification_status IN ('REQUIRES_VERIFICATION','SUGGESTED','USER_CONFIRMED','USER_REJECTED')),
    user_note TEXT,
    sort_order INTEGER NOT NULL DEFAULT 100,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (topic, code)
);
'''

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_baseline_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(BASELINE_SCHEMA)
    conn.commit()

def list_baseline_documents(conn: sqlite3.Connection, topic: str = "OT", status: Optional[str] = None, search: Optional[str] = None) -> list[dict]:
    sql = '''
        SELECT d.document_id, d.type_id, t.code AS type_code, t.title AS type_title,
        d.code, d.title, d.topic, d.category, d.lifecycle_stage,
        d.applicability_note, d.legal_basis_note, d.template_id,
        d.status, d.verification_status, d.user_note, d.sort_order
        FROM baseline_documents d JOIN document_types t ON d.type_id = t.type_id WHERE d.topic = ?
    '''
    params = [topic]
    if status:
        sql += " AND d.status = ? "
        params.append(status)
    if search:
        sql += " AND (d.title LIKE ? OR d.code LIKE ?) "
        like = f"%{search}%"
        params.extend([like, like])
    sql += " ORDER BY d.sort_order, d.code "
    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]

def update_baseline_status(conn, document_id, status, verification_status, user_note):
    conn.execute('''
        UPDATE baseline_documents
        SET status = ?, verification_status = ?, user_note = ?, updated_at = datetime('now')
        WHERE document_id = ?
    ''', (status, verification_status, user_note, document_id))
    conn.commit()

def count_baseline_by_status(conn, topic="OT"):
    rows = conn.execute("SELECT status, COUNT(*) AS cnt FROM baseline_documents WHERE topic = ? GROUP BY status", (topic,)).fetchall()
    result = {"total": 0, "SUGGESTED": 0, "USER_CONFIRMED": 0, "USER_REJECTED": 0, "REQUIRES_VERIFICATION": 0}
    for row in rows:
        result[row["status"]] = row["cnt"]
        result["total"] += row["cnt"]
    return result
