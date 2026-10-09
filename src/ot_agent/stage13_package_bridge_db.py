import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

BRIDGE_TABLE = "stage13_package_suggestions"

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS stage13_package_suggestions (
        suggestion_id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL,
        source_kind TEXT NOT NULL,
        source_id TEXT NOT NULL,
        proposed_topic TEXT NOT NULL DEFAULT 'OT',
        proposed_category TEXT NOT NULL DEFAULT 'TECHNICAL_PRELIMINARY',
        proposed_document_code TEXT NOT NULL,
        proposed_title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PRELIMINARY',
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        priority TEXT NOT NULL DEFAULT 'LOW',
        rationale TEXT,
        source_note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (company_id, source_kind, source_id, proposed_document_code)
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_stage13_package_suggestions_company
    ON stage13_package_suggestions(company_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_stage13_package_suggestions_source_kind
    ON stage13_package_suggestions(source_kind);
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_stage13_package_suggestions_status
    ON stage13_package_suggestions(status);
    """,
]


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_bridge_schema(conn: sqlite3.Connection) -> None:
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _distinct_values(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    company_id: str,
) -> List[str]:
    if not _table_exists(conn, table):
        return []

    cols = _table_columns(conn, table)

    if column not in cols or "company_id" not in cols:
        return []

    sql = f"""
        SELECT DISTINCT {column}
        FROM {table}
        WHERE company_id = ?
          AND {column} IS NOT NULL
          AND {column} <> ''
        ORDER BY {column}
    """

    rows = conn.execute(sql, (company_id,)).fetchall()
    return [_clean(row[0]) for row in rows if _clean(row[0])]


def _distinct_sout_factors(
    conn: sqlite3.Connection,
    company_id: str,
) -> List[str]:
    if not _table_exists(conn, "sout_results"):
        return []

    cols = _table_columns(conn, "sout_results")

    if "company_id" in cols:
        sql = """
            SELECT DISTINCT factor_id
            FROM sout_results
            WHERE company_id = ?
              AND factor_id IS NOT NULL
              AND factor_id <> ''
            ORDER BY factor_id
        """

        rows = conn.execute(sql, (company_id,)).fetchall()
        return [_clean(row[0]) for row in rows if _clean(row[0])]

    if not _table_exists(conn, "sout_workplaces"):
        return []

    sql = """
        SELECT DISTINCT sr.factor_id
        FROM sout_results sr
        JOIN sout_workplaces sw ON sr.workplace_id = sw.workplace_id
        WHERE sw.company_id = ?
          AND sr.factor_id IS NOT NULL
          AND sr.factor_id <> ''
        ORDER BY sr.factor_id
    """

    rows = conn.execute(sql, (company_id,)).fetchall()
    return [_clean(row[0]) for row in rows if _clean(row[0])]


def collect_suggestions(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    suggestions: List[Dict[str, Any]] = []

    companies = [
        row["company_id"]
        for row in conn.execute(
            "SELECT company_id FROM companies ORDER BY company_id"
        ).fetchall()
    ]

    for company_id in companies:
        for factor_id in _distinct_sout_factors(conn, company_id):
            doc_code = f"SOUT_FOLLOWUP_{factor_id}"
            suggestion_id = f"S13PS:{company_id}:SOUT:{factor_id}:{doc_code}"

            suggestions.append(
                {
                    "suggestion_id": suggestion_id,
                    "company_id": company_id,
                    "source_kind": "SOUT",
                    "source_id": factor_id,
                    "proposed_topic": "OT",
                    "proposed_category": "TECHNICAL_PRELIMINARY",
                    "proposed_document_code": doc_code,
                    "proposed_title": f"Preliminary SOUT follow-up for factor {factor_id}",
                    "status": "PRELIMINARY",
                    "verification_status": "REQUIRES_VERIFICATION",
                    "priority": "LOW",
                    "rationale": "Generated from synthetic sout_results metadata only.",
                    "source_note": "No legal requirement implied.",
                }
            )

        for risk_level_code in _distinct_values(
            conn,
            "risk_register",
            "risk_level_code",
            company_id,
        ):
            doc_code = f"RISK_CONTROL_{risk_level_code}"
            suggestion_id = f"S13PS:{company_id}:RISK:{risk_level_code}:{doc_code}"

            suggestions.append(
                {
                    "suggestion_id": suggestion_id,
                    "company_id": company_id,
                    "source_kind": "RISK",
                    "source_id": risk_level_code,
                    "proposed_topic": "OT",
                    "proposed_category": "TECHNICAL_PRELIMINARY",
                    "proposed_document_code": doc_code,
                    "proposed_title": f"Preliminary risk control package item for level {risk_level_code}",
                    "status": "PRELIMINARY",
                    "verification_status": "REQUIRES_VERIFICATION",
                    "priority": "LOW",
                    "rationale": "Generated from synthetic risk_register metadata only.",
                    "source_note": "No legal requirement implied.",
                }
            )

        for item_id in _distinct_values(
            conn,
            "ppe_norms",
            "item_id",
            company_id,
        ):
            doc_code = f"PPE_ISSUE_{item_id}"
            suggestion_id = f"S13PS:{company_id}:PPE:{item_id}:{doc_code}"

            suggestions.append(
                {
                    "suggestion_id": suggestion_id,
                    "company_id": company_id,
                    "source_kind": "PPE",
                    "source_id": item_id,
                    "proposed_topic": "OT",
                    "proposed_category": "TECHNICAL_PRELIMINARY",
                    "proposed_document_code": doc_code,
                    "proposed_title": f"Preliminary PPE issue/control package item for item {item_id}",
                    "status": "PRELIMINARY",
                    "verification_status": "REQUIRES_VERIFICATION",
                    "priority": "LOW",
                    "rationale": "Generated from synthetic ppe_norms metadata only.",
                    "source_note": "No legal requirement implied.",
                }
            )

    return suggestions


def insert_suggestions(
    conn: sqlite3.Connection,
    suggestions: List[Dict[str, Any]],
) -> int:
    inserted = 0

    for s in suggestions:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO stage13_package_suggestions (
                suggestion_id,
                company_id,
                source_kind,
                source_id,
                proposed_topic,
                proposed_category,
                proposed_document_code,
                proposed_title,
                status,
                verification_status,
                priority,
                rationale,
                source_note
            )
            VALUES (
                :suggestion_id,
                :company_id,
                :source_kind,
                :source_id,
                :proposed_topic,
                :proposed_category,
                :proposed_document_code,
                :proposed_title,
                :status,
                :verification_status,
                :priority,
                :rationale,
                :source_note
            )
            """,
            s,
        )

        inserted += int(cur.rowcount or 0)

    return inserted
