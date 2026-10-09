import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

SOURCE_TYPE = "STAGE13_PRELIMINARY"
REQUIRED_REQ_STATUS = "CONFIRMED"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _s(value: Any) -> str:
    return "" if value is None else str(value)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table: str) -> Dict[str, Any]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1]: row for row in rows}


def _insert_filtered(
    conn: sqlite3.Connection,
    table: str,
    values: Dict[str, Any],
) -> Dict[str, Any]:
    cols = _columns(conn, table)

    if not cols:
        raise ValueError(f"table missing or has no columns: {table}")

    filtered = {k: v for k, v in values.items() if k in cols}

    optional_defaults = {
        "author": values.get("author", "system"),
        "created_by": values.get("created_by", values.get("author", "system")),
        "updated_by": values.get("updated_by", values.get("author", "system")),
        "source": values.get("source", "STAGE13"),
        "source_type": values.get("source_type", "STAGE13"),
        "verification_status": values.get("verification_status", "REQUIRES_VERIFICATION"),
        "note": values.get("note", "Technical Stage 13 draft."),
        "user_note": values.get("user_note", ""),
        "comment": values.get("comment", ""),
    }

    for name in cols:
        if name not in filtered and name in optional_defaults:
            filtered[name] = optional_defaults[name]

    for name, info in cols.items():
        notnull = int(info[3] or 0)
        default = info[4]
        pk = int(info[5] or 0)

        if notnull and default is None and pk == 0 and name not in filtered:
            raise ValueError(f"missing required column {table}.{name}")

    if not filtered:
        raise ValueError(f"no insertable columns for {table}")

    col_list = ", ".join(filtered.keys())
    placeholders = ", ".join(["?"] * len(filtered))
    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    conn.execute(sql, list(filtered.values()))

    return filtered


def _update_filtered(
    conn: sqlite3.Connection,
    table: str,
    pk_column: str,
    pk_value: Any,
    values: Dict[str, Any],
) -> None:
    cols = _columns(conn, table)
    filtered = {
        k: v
        for k, v in values.items()
        if k in cols and k != pk_column
    }

    if not filtered:
        return

    assignments = ", ".join(f"{k}=?" for k in filtered)
    sql = f"UPDATE {table} SET {assignments} WHERE {pk_column}=?"
    conn.execute(sql, [*filtered.values(), pk_value])


def get_requirement(
    conn: sqlite3.Connection,
    requirement_id: str,
    company_id: str,
) -> Dict[str, Any]:
    if not _table_exists(conn, "document_requirements"):
        raise ValueError("document_requirements table missing")

    row = conn.execute(
        """
        SELECT *
        FROM document_requirements
        WHERE requirement_id = ?
          AND company_id = ?
        """,
        (requirement_id, company_id),
    ).fetchone()

    if row is None:
        raise ValueError("requirement not found or company mismatch")

    req = dict(row)

    if req.get("source_type") != SOURCE_TYPE:
        raise ValueError("not Stage 13 preliminary requirement")

    if req.get("status") != REQUIRED_REQ_STATUS:
        raise ValueError("requirement is not technically confirmed")

    return req


def _get_suggestion(
    conn: sqlite3.Connection,
    source_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    if not source_id:
        return None

    if not _table_exists(conn, "stage13_package_suggestions"):
        return None

    try:
        row = conn.execute(
            "SELECT * FROM stage13_package_suggestions WHERE suggestion_id = ?",
            (source_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return None

    return dict(row) if row is not None else None


def _build_content(
    req: Dict[str, Any],
    suggestion: Optional[Dict[str, Any]],
    draft_id: str,
    version_number: int,
    author: str,
    comment: str,
) -> str:
    clarify = "\u0423\u0422\u041e\u0427\u041d\u0418\u0422\u042c: requisites, dates, responsible persons, deadlines"
    no_source = "\u041d\u0415\u0422 \u0418\u0421\u0422\u041e\u0427\u041d\u0418\u041a\u0410: normative basis not loaded"
    requires = "\u0422\u0420\u0415\u0411\u0423\u0415\u0422 \u0412\u0415\u0420\u0418\u0424\u0418\u041a\u0410\u0426\u0418\u0418: occupational safety specialist"

    lines = [
        "TECHNICAL DRAFT / \u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0447\u0435\u0440\u043d\u043e\u0432\u0438\u043a",
        "",
        "This document is generated locally as a technical draft only.",
        "It is not a legally significant document and does not replace verification by an occupational safety specialist.",
        "",
        "--- METADATA ---",
        f"draft_id: {draft_id}",
        f"version_number: {version_number}",
        f"author: {author}",
        f"comment: {comment}",
        f"company_id: {_s(req.get('company_id'))}",
        f"requirement_id: {_s(req.get('requirement_id'))}",
        f"code: {_s(req.get('code'))}",
        f"title: {_s(req.get('title'))}",
        f"topic: {_s(req.get('topic') or 'OT')}",
        f"status: {_s(req.get('status'))}",
        f"priority: {_s(req.get('priority'))}",
        f"source_type: {_s(req.get('source_type'))}",
        f"source_id: {_s(req.get('source_id'))}",
        f"source_note: {_s(req.get('source_note'))}",
        f"user_note: {_s(req.get('user_note'))}",
        f"dependency_note: {_s(req.get('dependency_note'))}",
    ]

    if suggestion:
        lines.extend(
            [
                "",
                "--- STAGE 13 SUGGESTION METADATA ---",
                f"suggestion_id: {_s(suggestion.get('suggestion_id'))}",
                f"source_kind: {_s(suggestion.get('source_kind'))}",
                f"proposed_document_code: {_s(suggestion.get('proposed_document_code'))}",
                f"proposed_title: {_s(suggestion.get('proposed_title'))}",
                f"rationale: {_s(suggestion.get('rationale'))}",
                f"suggestion_source_note: {_s(suggestion.get('source_note'))}",
            ]
        )

    lines.extend(
        [
            "",
            "--- DRAFT BODY ---",
            "",
            f"[{clarify}]",
            f"[{no_source}]",
            f"[{requires}]",
            "",
            "Proposed technical structure:",
            "1. Header and internal identifiers.",
            "2. Scope and applicability note.",
            "3. Responsibilities placeholder.",
            "4. Procedure or requirement placeholder.",
            "5. Verification and approval placeholders.",
            "",
            "No normative claim is made by this draft.",
        ]
    )

    return "\n".join(lines)


def create_draft_from_requirement(
    conn: sqlite3.Connection,
    company_id: str,
    requirement_id: str,
    author: str = "user",
    comment: str = "",
    commit: bool = True,
) -> Dict[str, Any]:
    if not _table_exists(conn, "drafts"):
        raise ValueError("drafts table missing")

    if not _table_exists(conn, "draft_versions"):
        raise ValueError("draft_versions table missing")

    draft_cols = _columns(conn, "drafts")

    for required_col in ("draft_id", "company_id", "requirement_id"):
        if required_col not in draft_cols:
            raise ValueError(f"drafts.{required_col} missing")

    version_cols = _columns(conn, "draft_versions")

    for required_col in ("version_id", "draft_id", "version_number", "content"):
        if required_col not in version_cols:
            raise ValueError(f"draft_versions.{required_col} missing")

    req = get_requirement(conn, requirement_id, company_id)
    suggestion = _get_suggestion(conn, req.get("source_id"))
    now = _now()

    existing = conn.execute(
        """
        SELECT draft_id
        FROM drafts
        WHERE company_id = ?
          AND requirement_id = ?
        ORDER BY rowid
        LIMIT 1
        """,
        (company_id, requirement_id),
    ).fetchone()

    if existing is not None:
        draft_id = existing["draft_id"]

        max_version = conn.execute(
            "SELECT COALESCE(MAX(version_number), 0) FROM draft_versions WHERE draft_id = ?",
            (draft_id,),
        ).fetchone()[0]

        version_number = int(max_version or 0) + 1

        _update_filtered(
            conn,
            "drafts",
            "draft_id",
            draft_id,
            {
                "current_version": version_number,
                "updated_at": now,
                "status": "DRAFT",
            },
        )
    else:
        draft_id = str(uuid.uuid4())
        version_number = 1

        title = f"Stage13 technical draft: {_s(req.get('code') or req.get('title') or requirement_id)}"

        _insert_filtered(
            conn,
            "drafts",
            {
                "draft_id": draft_id,
                "company_id": company_id,
                "title": title,
                "topic": req.get("topic") or "OT",
                "document_type": req.get("code") or "STAGE13_PRELIMINARY",
                "requirement_id": requirement_id,
                "status": "DRAFT",
                "current_version": version_number,
                "created_at": now,
                "updated_at": now,
                "author": author,
                "note": "Technical Stage 13 draft. Requires verification.",
            },
        )

    content = _build_content(
        req,
        suggestion,
        draft_id,
        version_number,
        author,
        comment,
    )
    version_id = str(uuid.uuid4())

    _insert_filtered(
        conn,
        "draft_versions",
        {
            "version_id": version_id,
            "draft_id": draft_id,
            "version_number": version_number,
            "content": content,
            "author": author,
            "comment": comment or "Created from technically confirmed Stage 13 requirement.",
            "created_at": now,
        },
    )

    if commit:
        conn.commit()

    return {
        "draft_id": draft_id,
        "version_id": version_id,
        "version_number": version_number,
        "requirement_id": requirement_id,
        "company_id": company_id,
    }
