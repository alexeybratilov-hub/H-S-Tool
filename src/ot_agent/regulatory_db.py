from __future__ import annotations

import json
from typing import Any

from ot_agent.db import connect

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS regulatory_sources (
    source_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    doctype TEXT,
    issuer TEXT,
    approval_date TEXT,
    effective_date TEXT,
    status TEXT NOT NULL DEFAULT 'UNKNOWN',
    supersedes TEXT,
    superseded_by TEXT,
    topic TEXT NOT NULL DEFAULT 'OT',
    industry TEXT,
    file_path TEXT,
    text_path TEXT,
    sha256 TEXT,
    source_reference TEXT,
    retrieval_date TEXT,
    review_date TEXT,
    verified_by TEXT,
    verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
    comment TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS regulatory_chunks (
    chunk_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    heading_path TEXT,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    text TEXT NOT NULL,
    keywords TEXT,
    topic TEXT NOT NULL DEFAULT 'OT',
    obligation_type TEXT,
    applies_to_json TEXT,
    required_documents_json TEXT,
    status TEXT NOT NULL DEFAULT 'PARSED',
    confidence_tag TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES regulatory_sources(source_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_regulatory_sources_status
    ON regulatory_sources(status);

CREATE INDEX IF NOT EXISTS idx_regulatory_sources_topic
    ON regulatory_sources(topic);

CREATE INDEX IF NOT EXISTS idx_regulatory_sources_verification_status
    ON regulatory_sources(verification_status);

CREATE INDEX IF NOT EXISTS idx_regulatory_chunks_source_id
    ON regulatory_chunks(source_id);

CREATE INDEX IF NOT EXISTS idx_regulatory_chunks_topic
    ON regulatory_chunks(topic);

CREATE INDEX IF NOT EXISTS idx_regulatory_chunks_status
    ON regulatory_chunks(status);

CREATE INDEX IF NOT EXISTS idx_regulatory_chunks_confidence_tag
    ON regulatory_chunks(confidence_tag);
"""

ALLOWED_SOURCE_STATUSES = {
    "ACTIVE",
    "AMENDED",
    "SUPERSEDED",
    "DRAFT",
    "UNKNOWN",
}

ALLOWED_VERIFICATION_STATUSES = {
    "MANUAL_VERIFIED",
    "LLM_SUGGESTED",
    "REQUIRES_VERIFICATION",
    "REJECTED",
}

ALLOWED_CHUNK_STATUSES = {
    "RAW",
    "PARSED",
    "LLM_SUGGESTED",
    "RULE_GENERATED",
    "PRELIMINARY",
    "REQUIRES_VERIFICATION",
    "USER_VERIFIED",
    "APPROVED",
    "EXPORTED",
    "REJECTED",
    "SUPERSEDED",
    "ARCHIVED",
}

ALLOWED_CONFIDENCE_TAGS = {
    "MANUAL_VERIFIED",
    "LLM_SUGGESTED",
    "REQUIRES_VERIFICATION",
    "REJECTED",
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


def _validate_json_text(value: Any, field_name: str) -> str | None:
    value = _clean(value)

    if value is None:
        return None

    try:
        json.loads(str(value))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} is not valid JSON: {exc}") from exc

    return str(value)


def init_regulatory_schema() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def source_exists(source_id: str) -> bool:
    source_id = _clean(source_id)

    if not source_id:
        return False

    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM regulatory_sources WHERE source_id = ?",
            (str(source_id),),
        ).fetchone()

        return row is not None


def chunk_exists(chunk_id: str) -> bool:
    chunk_id = _clean(chunk_id)

    if not chunk_id:
        return False

    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM regulatory_chunks WHERE chunk_id = ?",
            (str(chunk_id),),
        ).fetchone()

        return row is not None


def create_source(data: dict[str, Any]) -> dict[str, Any]:
    source_id = _clean(data.get("source_id"))
    title = _clean(data.get("title"))

    if not source_id:
        raise ValueError("source_id is required.")

    if not title:
        raise ValueError("title is required.")

    if source_exists(str(source_id)):
        raise ValueError(f"Regulatory source already exists: {source_id}")

    status = _validate_choice(
        data.get("status"),
        ALLOWED_SOURCE_STATUSES,
        "status",
        default="UNKNOWN",
    )

    verification_status = _validate_choice(
        data.get("verification_status"),
        ALLOWED_VERIFICATION_STATUSES,
        "verification_status",
        default="REQUIRES_VERIFICATION",
    )

    topic = _clean(data.get("topic")) or "OT"

    payload = (
        str(source_id),
        str(title),
        _clean(data.get("doctype")),
        _clean(data.get("issuer")),
        _clean(data.get("approval_date")),
        _clean(data.get("effective_date")),
        status,
        _clean(data.get("supersedes")),
        _clean(data.get("supersedes_by")),
        topic,
        _clean(data.get("industry")),
        _clean(data.get("file_path")),
        _clean(data.get("text_path")),
        _clean(data.get("sha256")),
        _clean(data.get("source_reference")),
        _clean(data.get("retrieval_date")),
        _clean(data.get("review_date")),
        _clean(data.get("verified_by")),
        verification_status,
        _clean(data.get("comment")),
    )

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO regulatory_sources (
                source_id,
                title,
                doctype,
                issuer,
                approval_date,
                effective_date,
                status,
                supersedes,
                superseded_by,
                topic,
                industry,
                file_path,
                text_path,
                sha256,
                source_reference,
                retrieval_date,
                review_date,
                verified_by,
                verification_status,
                comment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
        conn.commit()

    created = get_source(str(source_id))

    if created is None:
        raise RuntimeError("Regulatory source was inserted but not found.")

    return created


def add_chunk(data: dict[str, Any]) -> dict[str, Any]:
    chunk_id = _clean(data.get("chunk_id"))
    source_id = _clean(data.get("source_id"))
    text = _clean(data.get("text"))

    if not chunk_id:
        raise ValueError("chunk_id is required.")

    if not source_id:
        raise ValueError("source_id is required.")

    if not text:
        raise ValueError("text is required.")

    if chunk_exists(str(chunk_id)):
        raise ValueError(f"Regulatory chunk already exists: {chunk_id}")

    if not source_exists(str(source_id)):
        raise ValueError(f"Regulatory source does not exist: {source_id}")

    chunk_index = data.get("chunk_index")

    if chunk_index is None:
        chunk_index = 0

    try:
        chunk_index = int(chunk_index)
    except (TypeError, ValueError) as exc:
        raise ValueError("chunk_index must be an integer.") from exc

    status = _validate_choice(
        data.get("status"),
        ALLOWED_CHUNK_STATUSES,
        "status",
        default="PARSED",
    )

    confidence_tag = _validate_choice(
        data.get("confidence_tag"),
        ALLOWED_CONFIDENCE_TAGS,
        "confidence_tag",
        default="REQUIRES_VERIFICATION",
    )

    topic = _clean(data.get("topic")) or "OT"

    applies_to_json = _validate_json_text(data.get("applies_to_json"), "applies_to_json")
    required_documents_json = _validate_json_text(
        data.get("required_documents_json"),
        "required_documents_json",
    )

    payload = (
        str(chunk_id),
        str(source_id),
        _clean(data.get("heading_path")),
        chunk_index,
        str(text),
        _clean(data.get("keywords")),
        topic,
        _clean(data.get("obligation_type")),
        applies_to_json,
        required_documents_json,
        status,
        confidence_tag,
    )

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO regulatory_chunks (
                chunk_id,
                source_id,
                heading_path,
                chunk_index,
                text,
                keywords,
                topic,
                obligation_type,
                applies_to_json,
                required_documents_json,
                status,
                confidence_tag
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
        conn.commit()

    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM regulatory_chunks WHERE chunk_id = ?",
            (str(chunk_id),),
        ).fetchone()

        if row is None:
            raise RuntimeError("Regulatory chunk was inserted but not found.")

        return dict(row)


def get_source(source_id: str) -> dict[str, Any] | None:
    source_id = _clean(source_id)

    if not source_id:
        return None

    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM regulatory_sources WHERE source_id = ?",
            (str(source_id),),
        ).fetchone()

        return dict(row) if row else None


def list_sources() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM regulatory_sources
            ORDER BY title, source_id
            """
        ).fetchall()

        return [dict(row) for row in rows]


def list_chunks(source_id: str | None = None) -> list[dict[str, Any]]:
    source_id = _clean(source_id)

    with connect() as conn:
        if source_id:
            rows = conn.execute(
                """
                SELECT
                    c.*,
                    s.title AS source_title,
                    s.status AS source_status,
                    s.verification_status AS source_verification_status
                FROM regulatory_chunks c
                JOIN regulatory_sources s
                    ON s.source_id = c.source_id
                WHERE c.source_id = ?
                ORDER BY c.chunk_index, c.chunk_id
                """,
                (str(source_id),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    c.*,
                    s.title AS source_title,
                    s.status AS source_status,
                    s.verification_status AS source_verification_status
                FROM regulatory_chunks c
                JOIN regulatory_sources s
                    ON s.source_id = c.source_id
                ORDER BY s.title, c.chunk_index, c.chunk_id
                """
            ).fetchall()

        return [dict(row) for row in rows]


def search_norms(query: str, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, int(limit))

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                s.source_id,
                s.title AS source_title,
                s.doctype,
                s.issuer,
                s.status AS source_status,
                s.verification_status,
                s.topic,
                c.chunk_id,
                c.heading_path,
                c.chunk_index,
                c.text,
                c.keywords,
                c.obligation_type,
                c.status AS chunk_status,
                c.confidence_tag
            FROM regulatory_chunks c
            JOIN regulatory_sources s
                ON s.source_id = c.source_id
            ORDER BY c.created_at DESC, c.chunk_id
            """
        ).fetchall()

    items = [dict(row) for row in rows]

    normalized_query = (query or "").strip().casefold()

    if normalized_query:
        terms = normalized_query.split()
        filtered: list[dict[str, Any]] = []

        for item in items:
            haystack = " ".join(
                str(item.get(field) or "")
                for field in (
                    "source_id",
                    "source_title",
                    "doctype",
                    "issuer",
                    "chunk_id",
                    "heading_path",
                    "text",
                    "keywords",
                    "obligation_type",
                )
            ).casefold()

            if all(term in haystack for term in terms):
                filtered.append(item)

        items = filtered

    return items[:limit]


def count_regulatory() -> dict[str, int]:
    with connect() as conn:
        sources = conn.execute(
            "SELECT COUNT(*) FROM regulatory_sources"
        ).fetchone()[0]

        chunks = conn.execute(
            "SELECT COUNT(*) FROM regulatory_chunks"
        ).fetchone()[0]

        requires_verification_sources = conn.execute(
            """
            SELECT COUNT(*)
            FROM regulatory_sources
            WHERE verification_status = 'REQUIRES_VERIFICATION'
            """
        ).fetchone()[0]

        requires_verification_chunks = conn.execute(
            """
            SELECT COUNT(*)
            FROM regulatory_chunks
            WHERE confidence_tag = 'REQUIRES_VERIFICATION'
            """
        ).fetchone()[0]

    return {
        "sources": int(sources),
        "chunks": int(chunks),
        "requires_verification_sources": int(requires_verification_sources),
        "requires_verification_chunks": int(requires_verification_chunks),
    }