import sqlite3
import uuid
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

REQUIREMENT_STATUS_VALUES = (
    "SUGGESTED",
    "CONFIRMED",
    "REJECTED",
    "REQUIRES_VERIFICATION",
)

PACKAGE_STATUS_VALUES = (
    "DRAFT",
    "USER_CONFIRMED",
    "USER_REJECTED",
    "REQUIRES_VERIFICATION",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS document_requirements (
    requirement_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(company_id),
    document_id TEXT REFERENCES baseline_documents(document_id),
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
        CHECK (status IN ('SUGGESTED','CONFIRMED','REJECTED','REQUIRES_VERIFICATION')),
    priority INTEGER NOT NULL DEFAULT 100,
    dependency_note TEXT,
    source_type TEXT,
    source_id TEXT,
    source_note TEXT,
    user_note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (company_id, code)
);

CREATE TABLE IF NOT EXISTS document_packages (
    package_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(company_id),
    name TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    status TEXT NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT','USER_CONFIRMED','USER_REJECTED','REQUIRES_VERIFICATION')),
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS package_items (
    package_id TEXT NOT NULL REFERENCES document_packages(package_id),
    requirement_id TEXT NOT NULL REFERENCES document_requirements(requirement_id),
    order_index INTEGER NOT NULL DEFAULT 100,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (package_id, requirement_id)
);
"""


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_package_schema(db_path: Optional[Path] = None) -> None:
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


def list_requirements(
    conn: sqlite3.Connection,
    company_id: str,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> list[dict]:
    sql = """
        SELECT
            requirement_id,
            company_id,
            document_id,
            code,
            title,
            topic,
            status,
            priority,
            dependency_note,
            source_type,
            source_id,
            source_note,
            user_note,
            created_at,
            updated_at
        FROM document_requirements
        WHERE company_id = ?
    """

    params: list = [company_id]

    if status:
        sql += " AND status = ?"
        params.append(status)

    if search:
        sql += " AND (title LIKE ? OR code LIKE ? OR requirement_id LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])

    sql += " ORDER BY priority, code"

    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def count_requirements_by_status(
    conn: sqlite3.Connection,
    company_id: str,
) -> dict:
    rows = conn.execute(
        """
        SELECT status, COUNT(*) AS cnt
        FROM document_requirements
        WHERE company_id = ?
        GROUP BY status
        """,
        (company_id,),
    ).fetchall()

    result = {status: 0 for status in REQUIREMENT_STATUS_VALUES}
    result["total"] = 0

    for row in rows:
        status = row["status"]
        count = row["cnt"]
        result[status] = count
        result["total"] += count

    return result


def generate_requirements_for_company(
    conn: sqlite3.Connection,
    company_id: str,
) -> int:
    if not conn.execute(
        "SELECT 1 FROM companies WHERE company_id = ?",
        (company_id,),
    ).fetchone():
        raise ValueError(f"company not found: {company_id}")

    docs = conn.execute(
        """
        SELECT
            document_id,
            code,
            title
        FROM baseline_documents
        WHERE topic = 'OT'
        ORDER BY sort_order, code
        """
    ).fetchall()

    count = 0

    for doc in docs:
        requirement_id = f"DR:{company_id}:{doc['code']}"

        conn.execute(
            """
            INSERT INTO document_requirements (
                requirement_id,
                company_id,
                document_id,
                code,
                title,
                topic,
                status,
                priority,
                source_type,
                source_id,
                source_note
            ) VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                'OT',
                'REQUIRES_VERIFICATION',
                100,
                'BASELINE_CATALOG',
                ?,
                'Synthetic requirement generated from baseline catalog. Requires verification.'
            )
            ON CONFLICT(requirement_id) DO UPDATE SET
                title = excluded.title,
                document_id = excluded.document_id,
                source_type = excluded.source_type,
                source_id = excluded.source_id,
                source_note = excluded.source_note,
                updated_at = datetime('now')
            """,
            (
                requirement_id,
                company_id,
                doc["document_id"],
                doc["code"],
                doc["title"],
                doc["document_id"],
            ),
        )

        count += 1

    return count


def update_requirement(
    conn: sqlite3.Connection,
    requirement_id: str,
    company_id: str,
    status: str,
    priority: int,
    dependency_note: Optional[str] = None,
    user_note: Optional[str] = None,
) -> None:
    if status not in REQUIREMENT_STATUS_VALUES:
        raise ValueError(f"invalid requirement status: {status}")

    cursor = conn.execute(
        """
        UPDATE document_requirements
        SET
            status = ?,
            priority = ?,
            dependency_note = ?,
            user_note = ?,
            updated_at = datetime('now')
        WHERE requirement_id = ?
          AND company_id = ?
        """,
        (
            status,
            int(priority),
            dependency_note,
            user_note,
            requirement_id,
            company_id,
        ),
    )

    if cursor.rowcount == 0:
        raise ValueError(
            f"requirement not found for company: {requirement_id} / {company_id}"
        )


def create_package(
    conn: sqlite3.Connection,
    company_id: str,
    name: str,
    note: Optional[str] = None,
) -> str:
    if not conn.execute(
        "SELECT 1 FROM companies WHERE company_id = ?",
        (company_id,),
    ).fetchone():
        raise ValueError(f"company not found: {company_id}")

    package_id = f"PKG:{company_id}:{uuid.uuid4().hex[:12]}"

    conn.execute(
        """
        INSERT INTO document_packages (
            package_id,
            company_id,
            name,
            topic,
            status,
            note
        ) VALUES (
            ?,
            ?,
            ?,
            'OT',
            'DRAFT',
            ?
        )
        """,
        (package_id, company_id, name, note),
    )

    return package_id


def populate_package_draft(
    conn: sqlite3.Connection,
    package_id: str,
) -> int:
    row = conn.execute(
        "SELECT company_id FROM document_packages WHERE package_id = ?",
        (package_id,),
    ).fetchone()

    if not row:
        raise ValueError(f"package not found: {package_id}")

    company_id = row["company_id"]

    conn.execute(
        "DELETE FROM package_items WHERE package_id = ?",
        (package_id,),
    )

    requirements = conn.execute(
        """
        SELECT requirement_id
        FROM document_requirements
        WHERE company_id = ?
          AND status != 'REJECTED'
        ORDER BY priority, code
        """,
        (company_id,),
    ).fetchall()

    for index, requirement in enumerate(requirements, start=1):
        conn.execute(
            """
            INSERT INTO package_items (
                package_id,
                requirement_id,
                order_index,
                note
            ) VALUES (
                ?,
                ?,
                ?,
                ?
            )
            """,
            (package_id, requirement["requirement_id"], index, None),
        )

    return len(requirements)


def list_packages(conn: sqlite3.Connection, company_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            p.package_id,
            p.name,
            p.status,
            p.note,
            p.created_at,
            p.updated_at,
            (
                SELECT COUNT(*)
                FROM package_items pi
                WHERE pi.package_id = p.package_id
            ) AS item_count
        FROM document_packages p
        WHERE p.company_id = ?
        ORDER BY p.created_at DESC
        """,
        (company_id,),
    ).fetchall()

    return [dict(row) for row in rows]


def list_package_items(conn: sqlite3.Connection, package_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            pi.order_index,
            r.requirement_id,
            r.code,
            r.title,
            r.status,
            r.priority,
            pi.note,
            pi.created_at,
            pi.updated_at
        FROM package_items pi
        JOIN document_requirements r ON pi.requirement_id = r.requirement_id
        WHERE pi.package_id = ?
        ORDER BY pi.order_index
        """,
        (package_id,),
    ).fetchall()

    return [dict(row) for row in rows]
