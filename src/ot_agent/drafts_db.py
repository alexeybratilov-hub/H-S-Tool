import difflib
import sqlite3
import uuid
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

DRAFT_STATUS_VALUES = ("DRAFT", "REQUIRES_VERIFICATION", "CONFIRMED", "REJECTED")
CORRECTION_STATUS_VALUES = ("PROPOSED", "ACTIVATED", "REJECTED")
RULE_STATUS_VALUES = ("ACTIVE", "INACTIVE")

SCHEMA = """
CREATE TABLE IF NOT EXISTS drafts (
    draft_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(company_id),
    title TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    document_type TEXT,
    requirement_id TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT','REQUIRES_VERIFICATION','CONFIRMED','REJECTED')),
    current_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS draft_versions (
    version_id TEXT PRIMARY KEY,
    draft_id TEXT NOT NULL REFERENCES drafts(draft_id),
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    author TEXT,
    comment TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (draft_id, version_number)
);

CREATE TABLE IF NOT EXISTS version_diffs (
    diff_id TEXT PRIMARY KEY,
    draft_id TEXT NOT NULL REFERENCES drafts(draft_id),
    from_version INTEGER NOT NULL,
    to_version INTEGER NOT NULL,
    diff_text TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (draft_id, from_version, to_version)
);

CREATE TABLE IF NOT EXISTS corrections (
    correction_id TEXT PRIMARY KEY,
    draft_id TEXT NOT NULL REFERENCES drafts(draft_id),
    from_version INTEGER NOT NULL,
    to_version INTEGER NOT NULL,
    category TEXT,
    old_snippet TEXT,
    new_snippet TEXT,
    comment TEXT,
    proposed_rule TEXT,
    status TEXT NOT NULL DEFAULT 'PROPOSED'
        CHECK (status IN ('PROPOSED','ACTIVATED','REJECTED')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS active_rules (
    rule_id TEXT PRIMARY KEY,
    company_id TEXT REFERENCES companies(company_id),
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    rule_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE','INACTIVE')),
    source_correction_id TEXT REFERENCES corrections(correction_id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_draft_schema(db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def list_companies(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            company_id,
            COALESCE(
                NULLIF(short_name, ''),
                NULLIF(legal_name, ''),
                company_id
            ) AS display_name
        FROM companies
        ORDER BY display_name
        """
    ).fetchall()
    return [dict(row) for row in rows]


def create_draft(
    conn: sqlite3.Connection,
    company_id: str,
    title: str,
    document_type: Optional[str] = None,
    requirement_id: Optional[str] = None,
    initial_content: str = "",
) -> str:
    if not conn.execute(
        "SELECT 1 FROM companies WHERE company_id = ?",
        (company_id,),
    ).fetchone():
        raise ValueError(f"company not found: {company_id}")

    draft_id = f"DRF:{company_id}:{uuid.uuid4().hex[:12]}"

    conn.execute(
        """
        INSERT INTO drafts (
            draft_id,
            company_id,
            title,
            topic,
            document_type,
            requirement_id,
            status,
            current_version
        ) VALUES (?, ?, ?, 'OT', ?, ?, 'DRAFT', 1)
        """,
        (draft_id, company_id, title, document_type, requirement_id),
    )

    version_id = f"DV:{uuid.uuid4().hex[:12]}"
    conn.execute(
        """
        INSERT INTO draft_versions (
            version_id,
            draft_id,
            version_number,
            content,
            author,
            comment
        ) VALUES (?, ?, 1, ?, 'system', 'initial')
        """,
        (version_id, draft_id, initial_content or ""),
    )

    return draft_id


def _get_version_content(conn: sqlite3.Connection, draft_id: str, version_number: int) -> str:
    row = conn.execute(
        """
        SELECT content
        FROM draft_versions
        WHERE draft_id = ?
          AND version_number = ?
        """,
        (draft_id, version_number),
    ).fetchone()
    return row["content"] if row else ""


def add_version(
    conn: sqlite3.Connection,
    draft_id: str,
    content: str,
    author: str = "user",
    comment: str = "",
) -> int:
    row = conn.execute(
        "SELECT current_version FROM drafts WHERE draft_id = ?",
        (draft_id,),
    ).fetchone()

    if not row:
        raise ValueError(f"draft not found: {draft_id}")

    previous_version = int(row["current_version"])
    previous_content = _get_version_content(conn, draft_id, previous_version)
    new_version = previous_version + 1

    version_id = f"DV:{uuid.uuid4().hex[:12]}"
    conn.execute(
        """
        INSERT INTO draft_versions (
            version_id,
            draft_id,
            version_number,
            content,
            author,
            comment
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (version_id, draft_id, new_version, content or "", author, comment),
    )

    conn.execute(
        """
        UPDATE drafts
        SET current_version = ?,
            updated_at = datetime('now')
        WHERE draft_id = ?
        """,
        (new_version, draft_id),
    )

    diff_text = "".join(
        difflib.unified_diff(
            previous_content.splitlines(keepends=True),
            (content or "").splitlines(keepends=True),
            fromfile=f"v{previous_version}",
            tofile=f"v{new_version}",
            lineterm="",
        )
    )

    diff_id = f"VD:{uuid.uuid4().hex[:12]}"
    conn.execute(
        """
        INSERT OR REPLACE INTO version_diffs (
            diff_id,
            draft_id,
            from_version,
            to_version,
            diff_text
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (diff_id, draft_id, previous_version, new_version, diff_text),
    )

    return new_version


def list_drafts(conn: sqlite3.Connection, company_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT *
        FROM drafts
        WHERE company_id = ?
        ORDER BY updated_at DESC
        """,
        (company_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_draft(conn: sqlite3.Connection, draft_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM drafts WHERE draft_id = ?",
        (draft_id,),
    ).fetchone()
    return dict(row) if row else None


def list_versions(conn: sqlite3.Connection, draft_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            version_id,
            version_number,
            content,
            author,
            comment,
            created_at
        FROM draft_versions
        WHERE draft_id = ?
        ORDER BY version_number
        """,
        (draft_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def list_diffs(conn: sqlite3.Connection, draft_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            diff_id,
            from_version,
            to_version,
            diff_text,
            created_at
        FROM version_diffs
        WHERE draft_id = ?
        ORDER BY to_version DESC, from_version DESC
        """,
        (draft_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_latest_diff(conn: sqlite3.Connection, draft_id: str) -> Optional[dict]:
    diffs = list_diffs(conn, draft_id)
    return diffs[0] if diffs else None


def add_correction(
    conn: sqlite3.Connection,
    draft_id: str,
    from_version: int,
    to_version: int,
    category: Optional[str] = None,
    old_snippet: Optional[str] = None,
    new_snippet: Optional[str] = None,
    comment: Optional[str] = None,
    proposed_rule: Optional[str] = None,
) -> str:
    if not conn.execute(
        "SELECT 1 FROM drafts WHERE draft_id = ?",
        (draft_id,),
    ).fetchone():
        raise ValueError(f"draft not found: {draft_id}")

    if to_version <= from_version:
        raise ValueError("to_version must be greater than from_version")

    correction_id = f"CR:{uuid.uuid4().hex[:12]}"

    conn.execute(
        """
        INSERT INTO corrections (
            correction_id,
            draft_id,
            from_version,
            to_version,
            category,
            old_snippet,
            new_snippet,
            comment,
            proposed_rule,
            status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PROPOSED')
        """,
        (
            correction_id,
            draft_id,
            int(from_version),
            int(to_version),
            category,
            old_snippet,
            new_snippet,
            comment,
            proposed_rule,
        ),
    )

    return correction_id


def list_corrections(conn: sqlite3.Connection, draft_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT *
        FROM corrections
        WHERE draft_id = ?
        ORDER BY created_at DESC
        """,
        (draft_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def activate_rule(conn: sqlite3.Connection, correction_id: str) -> str:
    row = conn.execute(
        """
        SELECT
            c.correction_id,
            c.status,
            c.proposed_rule,
            c.comment,
            d.company_id,
            d.topic
        FROM corrections c
        JOIN drafts d ON c.draft_id = d.draft_id
        WHERE c.correction_id = ?
        """,
        (correction_id,),
    ).fetchone()

    if not row:
        raise ValueError(f"correction not found: {correction_id}")

    if row["status"] == "ACTIVATED":
        return row["correction_id"]

    rule_text = (row["proposed_rule"] or row["comment"] or "").strip()
    if not rule_text:
        raise ValueError("empty rule text")

    rule_id = f"AR:{uuid.uuid4().hex[:12]}"

    conn.execute(
        """
        INSERT INTO active_rules (
            rule_id,
            company_id,
            topic,
            rule_text,
            status,
            source_correction_id
        ) VALUES (?, ?, ?, ?, 'ACTIVE', ?)
        """,
        (rule_id, row["company_id"], row["topic"], rule_text, correction_id),
    )

    conn.execute(
        """
        UPDATE corrections
        SET status = 'ACTIVATED'
        WHERE correction_id = ?
        """,
        (correction_id,),
    )

    return rule_id


def list_active_rules(
    conn: sqlite3.Connection,
    company_id: Optional[str] = None,
    topic: str = "OT",
) -> list[dict]:
    sql = """
        SELECT *
        FROM active_rules
        WHERE status = 'ACTIVE'
          AND topic = ?
    """
    params: list = [topic]

    if company_id:
        sql += " AND (company_id IS NULL OR company_id = ?)"
        params.append(company_id)

    sql += " ORDER BY created_at DESC"

    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]
