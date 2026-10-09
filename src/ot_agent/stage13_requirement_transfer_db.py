import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

SOURCE_TYPE = "STAGE13_PRELIMINARY"
TARGET_STATUS = "REQUIRES_VERIFICATION"
TARGET_TOPIC = "OT"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:32]
    return f"{prefix}{digest}"


def _columns(conn: sqlite3.Connection, table: str) -> List[Dict[str, Any]]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [
        {
            "cid": row[0],
            "name": row[1],
            "type": row[2],
            "notnull": int(row[3] or 0),
            "default": row[4],
            "pk": int(row[5] or 0),
        }
        for row in rows
    ]


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _resolve_document_id(
    conn: sqlite3.Connection,
    code: str,
    title: str,
) -> Optional[str]:
    if not _table_exists(conn, "baseline_documents"):
        return None

    row = conn.execute(
        "SELECT document_id FROM baseline_documents WHERE code = ? COLLATE NOCASE LIMIT 1",
        (code,),
    ).fetchone()

    if row is not None:
        return row[0]

    row = conn.execute(
        "SELECT document_id FROM baseline_documents WHERE title = ? COLLATE NOCASE LIMIT 1",
        (title,),
    ).fetchone()

    if row is not None:
        return row[0]

    return None


def _is_required_without_default(col: Dict[str, Any]) -> bool:
    return int(col.get("notnull", 0)) == 1 and col.get("default") is None and int(col.get("pk", 0)) == 0


def plan_transfer(conn: sqlite3.Connection) -> Tuple[List[Dict[str, Any]], List[str]]:
    issues: List[str] = []
    rows: List[Dict[str, Any]] = []

    if not _table_exists(conn, "stage13_package_suggestions"):
        issues.append("stage13_package_suggestions table missing")
        return rows, issues

    if not _table_exists(conn, "document_requirements"):
        issues.append("document_requirements table missing")
        return rows, issues

    req_cols = _columns(conn, "document_requirements")
    req_names = {col["name"]: col for col in req_cols}

    necessary = [
        "requirement_id",
        "company_id",
        "code",
        "title",
        "topic",
        "status",
        "priority",
        "source_type",
        "source_id",
    ]

    missing = [name for name in necessary if name not in req_names]

    if missing:
        issues.append("document_requirements missing columns: " + ",".join(missing))
        return rows, issues

    existing_ids = {
        row[0]
        for row in conn.execute("SELECT requirement_id FROM document_requirements").fetchall()
    }

    existing_sources = {
        (row[0], row[1])
        for row in conn.execute(
            """
            SELECT company_id, source_id
            FROM document_requirements
            WHERE source_type = ?
            """,
            (SOURCE_TYPE,),
        ).fetchall()
    }

    suggestions = conn.execute(
        """
        SELECT *
        FROM stage13_package_suggestions
        ORDER BY company_id, source_kind, proposed_document_code
        """
    ).fetchall()

    if not suggestions:
        issues.append("stage13_package_suggestions is empty")
        return rows, issues

    now = _now()

    for suggestion in suggestions:
        suggestion_id = str(suggestion["suggestion_id"])
        company_id = str(suggestion["company_id"])
        code = str(suggestion["proposed_document_code"])
        title = str(suggestion["proposed_title"])
        priority = str(suggestion["priority"] or "LOW")
        rationale = str(suggestion["rationale"] or "")
        source_note = str(suggestion["source_note"] or "")

        requirement_id = _stable_id("DR:S13:", suggestion_id)

        if requirement_id in existing_ids:
            issues.append(f"duplicate requirement_id for suggestion {suggestion_id}")
            continue

        if (company_id, suggestion_id) in existing_sources:
            issues.append(f"suggestion already transferred: {suggestion_id}")
            continue

        document_id = None

        if "document_id" in req_names:
            document_id = _resolve_document_id(conn, code, title)

            if document_id is None and _is_required_without_default(req_names["document_id"]):
                issues.append(f"cannot resolve required document_id for suggestion {suggestion_id}")
                continue

        values: Dict[str, Any] = {
            "requirement_id": requirement_id,
            "company_id": company_id,
            "document_id": document_id,
            "code": code,
            "title": title,
            "topic": TARGET_TOPIC,
            "status": TARGET_STATUS,
            "priority": priority,
            "dependency_note": rationale,
            "source_type": SOURCE_TYPE,
            "source_id": suggestion_id,
            "source_note": source_note,
            "user_note": "Transferred from stage13_package_suggestions. Requires OT specialist verification.",
            "created_at": now,
            "updated_at": now,
        }

        for col in req_cols:
            name = col["name"]

            if _is_required_without_default(col):
                if name not in values or values[name] is None:
                    issues.append(f"required column cannot be populated for suggestion {suggestion_id}: {name}")

        if any(issue.startswith("required column cannot be populated") for issue in issues[-1:]):
            continue

        row = {name: values[name] for name in req_names if name in values}
        rows.append(row)

    return rows, issues


def insert_rows(conn: sqlite3.Connection, rows: List[Dict[str, Any]]) -> int:
    inserted = 0

    for row in rows:
        cols = list(row.keys())
        placeholders = ", ".join(["?"] * len(cols))
        col_list = ", ".join(cols)
        sql = f"INSERT INTO document_requirements ({col_list}) VALUES ({placeholders})"
        conn.execute(sql, [row[col] for col in cols])
        inserted += 1

    return inserted


def validate_transfer(conn: sqlite3.Connection) -> List[str]:
    errors: List[str] = []

    if not _table_exists(conn, "document_requirements"):
        return ["document_requirements table missing"]

    req_cols = {col["name"] for col in _columns(conn, "document_requirements")}

    if "source_type" not in req_cols:
        return ["document_requirements.source_type missing"]

    rows = conn.execute(
        "SELECT COUNT(*) FROM document_requirements WHERE source_type = ?",
        (SOURCE_TYPE,),
    ).fetchone()[0]

    if rows <= 0:
        errors.append("no transferred requirements found")

    if "status" in req_cols:
        bad_status = conn.execute(
            """
            SELECT COUNT(*)
            FROM document_requirements
            WHERE source_type = ?
              AND status <> ?
            """,
            (SOURCE_TYPE, TARGET_STATUS),
        ).fetchone()[0]

        if bad_status:
            errors.append("transferred requirements with unexpected status")

    if "company_id" in req_cols:
        orphan = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM document_requirements
            WHERE source_type = ?
              AND (
                company_id IS NULL
                OR company_id NOT IN (SELECT company_id FROM companies)
              )
            """,
            (SOURCE_TYPE,),
        ).fetchone()[0]

        if orphan:
            errors.append("transferred requirements with orphan company_id")

    if "requirement_id" in req_cols:
        dup = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM (
              SELECT requirement_id
              FROM document_requirements
              WHERE source_type = ?
              GROUP BY requirement_id
              HAVING COUNT(*) > 1
            )
            """,
            (SOURCE_TYPE,),
        ).fetchone()[0]

        if dup:
            errors.append("duplicate transferred requirement_id rows")

    if "source_id" in req_cols:
        dup_source = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM (
              SELECT company_id, source_id
              FROM document_requirements
              WHERE source_type = ?
              GROUP BY company_id, source_id
              HAVING COUNT(*) > 1
            )
            """,
            (SOURCE_TYPE,),
        ).fetchone()[0]

        if dup_source:
            errors.append("duplicate transferred source_id rows")

    return errors
