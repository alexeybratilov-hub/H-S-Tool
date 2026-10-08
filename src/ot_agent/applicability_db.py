from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ot_agent.db import connect

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS norm_applicability (
    applicability_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL DEFAULT '',
    applicability_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
    reason TEXT,
    confirmed_by TEXT,
    confirmed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES regulatory_sources(source_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_norm_applicability_unique
    ON norm_applicability(company_id, source_id, chunk_id);

CREATE INDEX IF NOT EXISTS idx_norm_applicability_company_id
    ON norm_applicability(company_id);

CREATE INDEX IF NOT EXISTS idx_norm_applicability_source_id
    ON norm_applicability(source_id);
"""

ALLOWED_APPLICABILITY_STATUSES = {
    "SUGGESTED",
    "CONFIRMED",
    "REJECTED",
    "REQUIRES_VERIFICATION",
}


def _clean(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    return value


def _upper(value: Any) -> str | None:
    value = _clean(value)

    if value is None:
        return None

    return str(value).upper()


def _validate_choice(
    value: Any,
    allowed: set[str],
    field_name: str,
    default: str | None = None,
) -> str:
    value = _upper(value)

    if value is None:
        if default is None:
            raise ValueError(f"{field_name} is required.")
        return default

    if value not in allowed:
        raise ValueError(
            f"{field_name} has unsupported value: {value}. "
            f"Allowed values: {', '.join(sorted(allowed))}."
        )

    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _make_applicability_id(company_id: str, source_id: str, chunk_id: str = "") -> str:
    return f"{company_id}::{source_id}::{chunk_id}"


def init_applicability_schema() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def get_applicability(
    company_id: str,
    source_id: str,
    chunk_id: str = "",
) -> dict[str, Any] | None:
    company_id = _clean(company_id)
    source_id = _clean(source_id)
    chunk_id = _clean(chunk_id) or ""

    if not company_id or not source_id:
        return None

    applicability_id = _make_applicability_id(
        str(company_id),
        str(source_id),
        str(chunk_id),
    )

    with connect() as conn:
        row = conn.execute(
            """
            SELECT
                a.*,
                s.title AS source_title,
                s.status AS source_status,
                s.verification_status AS source_verification_status
            FROM norm_applicability a
            JOIN regulatory_sources s
                ON s.source_id = a.source_id
            WHERE a.applicability_id = ?
            """,
            (applicability_id,),
        ).fetchone()

        return dict(row) if row else None


def list_applicability(company_id: str | None = None) -> list[dict[str, Any]]:
    company_id = _clean(company_id)

    with connect() as conn:
        if company_id:
            rows = conn.execute(
                """
                SELECT
                    a.*,
                    s.title AS source_title,
                    s.status AS source_status,
                    s.verification_status AS source_verification_status
                FROM norm_applicability a
                JOIN regulatory_sources s
                    ON s.source_id = a.source_id
                WHERE a.company_id = ?
                ORDER BY s.title, a.source_id, a.chunk_id
                """,
                (str(company_id),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    a.*,
                    s.title AS source_title,
                    s.status AS source_status,
                    s.verification_status AS source_verification_status
                FROM norm_applicability a
                JOIN regulatory_sources s
                    ON s.source_id = a.source_id
                ORDER BY a.company_id, s.title, a.source_id, a.chunk_id
                """
            ).fetchall()

        return [dict(row) for row in rows]


def list_sources_with_applicability(company_id: str) -> list[dict[str, Any]]:
    company_id = _clean(company_id)

    if not company_id:
        return []

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                s.source_id,
                s.title AS source_title,
                s.status AS source_status,
                s.verification_status AS source_verification_status,
                a.applicability_id,
                a.chunk_id,
                a.applicability_status,
                a.reason,
                a.confirmed_by,
                a.confirmed_at,
                a.updated_at
            FROM regulatory_sources s
            LEFT JOIN norm_applicability a
                ON a.source_id = s.source_id
                AND a.company_id = ?
                AND a.chunk_id = ''
            ORDER BY s.title, s.source_id
            """,
            (str(company_id),),
        ).fetchall()

        return [dict(row) for row in rows]


def upsert_applicability(data: dict[str, Any]) -> dict[str, Any]:
    company_id = _clean(data.get("company_id"))
    source_id = _clean(data.get("source_id"))

    if not company_id:
        raise ValueError("company_id is required.")

    if not source_id:
        raise ValueError("source_id is required.")

    chunk_id = _clean(data.get("chunk_id")) or ""

    status = _validate_choice(
        data.get("applicability_status"),
        ALLOWED_APPLICABILITY_STATUSES,
        "applicability_status",
        default="REQUIRES_VERIFICATION",
    )

    reason = _clean(data.get("reason"))
    confirmed_by = _clean(data.get("confirmed_by"))
    confirmed_at = _clean(data.get("confirmed_at"))

    applicability_id = _make_applicability_id(
        str(company_id),
        str(source_id),
        str(chunk_id),
    )

    existing = get_applicability(
        str(company_id),
        str(source_id),
        str(chunk_id),
    )

    if status == "CONFIRMED":
        if not confirmed_by:
            confirmed_by = "USER"

        if not confirmed_at:
            confirmed_at = _utc_now()
    else:
        if existing and not confirmed_at:
            confirmed_at = existing.get("confirmed_at")

    with connect() as conn:
        if existing:
            conn.execute(
                """
                UPDATE norm_applicability
                SET
                    applicability_status = ?,
                    reason = ?,
                    confirmed_by = ?,
                    confirmed_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE applicability_id = ?
                """,
                (
                    status,
                    str(reason) if reason else None,
                    str(confirmed_by) if confirmed_by else None,
                    str(confirmed_at) if confirmed_at else None,
                    applicability_id,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO norm_applicability (
                    applicability_id,
                    company_id,
                    source_id,
                    chunk_id,
                    applicability_status,
                    reason,
                    confirmed_by,
                    confirmed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    applicability_id,
                    str(company_id),
                    str(source_id),
                    str(chunk_id),
                    status,
                    str(reason) if reason else None,
                    str(confirmed_by) if confirmed_by else None,
                    str(confirmed_at) if confirmed_at else None,
                ),
            )

        conn.commit()

    result = get_applicability(
        str(company_id),
        str(source_id),
        str(chunk_id),
    )

    if result is None:
        raise RuntimeError("Applicability record was saved but not found.")

    return result


def count_applicability(company_id: str) -> dict[str, int]:
    company_id = _clean(company_id)

    result = {
        "total": 0,
        "SUGGESTED": 0,
        "CONFIRMED": 0,
        "REJECTED": 0,
        "REQUIRES_VERIFICATION": 0,
    }

    if not company_id:
        return result

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                applicability_status,
                COUNT(*) AS cnt
            FROM norm_applicability
            WHERE company_id = ?
            GROUP BY applicability_status
            """,
            (str(company_id),),
        ).fetchall()

    total = 0

    for row in rows:
        status = str(row["applicability_status"])
        count = int(row["cnt"])

        if status in result:
            result[status] = count

        total += count

    result["total"] = total

    return result


def list_applicable_source_ids(
    company_id: str,
    statuses: tuple[str, ...] = ("CONFIRMED",),
) -> list[str]:
    company_id = _clean(company_id)

    if not company_id:
        return []

    normalized_statuses: list[str] = []

    for status in statuses:
        validated = _validate_choice(
            status,
            ALLOWED_APPLICABILITY_STATUSES,
            "status",
        )
        normalized_statuses.append(validated)

    if not normalized_statuses:
        return []

    placeholders = ", ".join("?" for _ in normalized_statuses)

    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT DISTINCT source_id
            FROM norm_applicability
            WHERE company_id = ?
              AND applicability_status IN ({placeholders})
            ORDER BY source_id
            """,
            (str(company_id), *normalized_statuses),
        ).fetchall()

        return [str(row["source_id"]) for row in rows]