import sqlite3
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS responsibility_roles (
    role_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    description TEXT,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS responsibility_assignments (
    assignment_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(company_id),
    role_id TEXT NOT NULL REFERENCES responsibility_roles(role_id),
    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
    status TEXT NOT NULL DEFAULT 'PROPOSED'
        CHECK (status IN ('PROPOSED','CONFIRMED','MISSING_EVIDENCE','REQUIRES_VERIFICATION','REJECTED')),
    evidence_note TEXT,
    confirmed_by TEXT,
    comment TEXT,
    valid_from TEXT,
    valid_until TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (company_id, role_id, employee_id)
);
"""

ROLE_CODES = [
    "HEAD_ORGANIZATION",
    "DEPUTY_HEAD",
    "OT_RESPONSIBLE",
    "OT_COMMISSION_CHAIR",
    "OT_COMMISSION_MEMBER",
    "TRAINING_RESPONSIBLE",
    "BRIEFING_RESPONSIBLE",
    "KNOWLEDGE_CHECK_COMMISSION_CHAIR",
    "MEDICAL_EXAM_RESPONSIBLE",
    "PSYCHIATRIC_EXAM_RESPONSIBLE",
    "PPE_RESPONSIBLE",
    "SOUT_RESPONSIBLE",
    "RISK_ASSESSMENT_RESPONSIBLE",
    "ELECTRICAL_RESPONSIBLE",
]

STATUS_VALUES = (
    "PROPOSED",
    "CONFIRMED",
    "MISSING_EVIDENCE",
    "REQUIRES_VERIFICATION",
    "REJECTED",
)


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _seed_roles(conn: sqlite3.Connection) -> None:
    for code in ROLE_CODES:
        role_id = f"ROLE_{code}"
        conn.execute(
            """
            INSERT INTO responsibility_roles (
                role_id,
                code,
                title,
                topic,
                description,
                active
            ) VALUES (
                ?,
                ?,
                ?,
                'OT',
                ?,
                1
            )
            ON CONFLICT(role_id) DO UPDATE SET
                code = excluded.code,
                title = excluded.title,
                topic = excluded.topic,
                description = excluded.description,
                updated_at = datetime('now')
            """,
            (
                role_id,
                code,
                code,
                "Synthetic technical role. Requires verification.",
            ),
        )


def init_responsibility_schema(db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        _seed_roles(conn)
        conn.commit()
    finally:
        conn.close()


def list_roles(conn: sqlite3.Connection, topic: str = "OT") -> list[dict]:
    rows = conn.execute(
        """
        SELECT
            role_id,
            code,
            title,
            topic,
            description,
            active
        FROM responsibility_roles
        WHERE topic = ?
          AND active = 1
        ORDER BY code
        """,
        (topic,),
    ).fetchall()

    return [dict(row) for row in rows]


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


def _employee_display_expr(conn: sqlite3.Connection) -> str:
    rows = conn.execute("PRAGMA table_info(employees)").fetchall()
    cols = {str(row[1]).lower(): row[1] for row in rows}

    candidates = [
        "full_name",
        "fio",
        "name",
        "employee_name",
        "surname",
        "last_name",
    ]

    for candidate in candidates:
        if candidate in cols:
            return f"e.{cols[candidate]}"

    return "e.employee_id"


def list_employees(conn: sqlite3.Connection, company_id: str) -> list[dict]:
    expr = _employee_display_expr(conn)
    sql = f"""
        SELECT
            e.employee_id,
            {expr} AS display_name
        FROM employees e
        WHERE e.company_id = ?
        ORDER BY display_name
    """
    rows = conn.execute(sql, (company_id,)).fetchall()
    return [dict(row) for row in rows]

def list_assignments(
    conn: sqlite3.Connection,
    company_id: str,
    status: Optional[str] = None,
) -> list[dict]:
    expr = _employee_display_expr(conn)

    sql = f"""
        SELECT
            a.assignment_id,
            a.company_id,
            r.role_id,
            r.code AS role_code,
            r.title AS role_title,
            a.employee_id,
            {expr} AS employee_display,
            a.status,
            a.evidence_note,
            a.confirmed_by,
            a.comment,
            a.valid_from,
            a.valid_until,
            a.updated_at
        FROM responsibility_assignments a
        JOIN responsibility_roles r ON a.role_id = r.role_id
        JOIN employees e ON a.employee_id = e.employee_id
        WHERE a.company_id = ?
    """

    params: list = [company_id]

    if status:
        sql += " AND a.status = ?"
        params.append(status)

    sql += " ORDER BY r.code, employee_display"

    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def count_assignments_by_status(
    conn: sqlite3.Connection,
    company_id: str,
) -> dict:
    rows = conn.execute(
        """
        SELECT status, COUNT(*) AS cnt
        FROM responsibility_assignments
        WHERE company_id = ?
        GROUP BY status
        """,
        (company_id,),
    ).fetchall()

    result = {status: 0 for status in STATUS_VALUES}
    result["total"] = 0

    for row in rows:
        status = row["status"]
        count = row["cnt"]
        result[status] = count
        result["total"] += count

    return result


def _validate_status(status: str) -> None:
    if status not in STATUS_VALUES:
        raise ValueError(f"invalid status: {status}")


def upsert_assignment(
    conn: sqlite3.Connection,
    company_id: str,
    role_id: str,
    employee_id: str,
    status: str,
    evidence_note: Optional[str] = None,
    confirmed_by: Optional[str] = None,
    comment: Optional[str] = None,
    valid_from: Optional[str] = None,
    valid_until: Optional[str] = None,
) -> None:
    _validate_status(status)

    if not conn.execute(
        "SELECT 1 FROM responsibility_roles WHERE role_id = ?",
        (role_id,),
    ).fetchone():
        raise ValueError(f"role not found: {role_id}")

    if not conn.execute(
        "SELECT 1 FROM companies WHERE company_id = ?",
        (company_id,),
    ).fetchone():
        raise ValueError(f"company not found: {company_id}")

    if not conn.execute(
        """
        SELECT 1
        FROM employees
        WHERE employee_id = ?
          AND company_id = ?
        """,
        (employee_id, company_id),
    ).fetchone():
        raise ValueError(
            f"employee {employee_id} does not belong to company {company_id}"
        )

    assignment_id = f"RA:{company_id}:{role_id}:{employee_id}"

    conn.execute(
        """
        INSERT INTO responsibility_assignments (
            assignment_id,
            company_id,
            role_id,
            employee_id,
            status,
            evidence_note,
            confirmed_by,
            comment,
            valid_from,
            valid_until
        ) VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        ON CONFLICT(assignment_id) DO UPDATE SET
            status = excluded.status,
            evidence_note = excluded.evidence_note,
            confirmed_by = excluded.confirmed_by,
            comment = excluded.comment,
            valid_from = excluded.valid_from,
            valid_until = excluded.valid_until,
            updated_at = datetime('now')
        """,
        (
            assignment_id,
            company_id,
            role_id,
            employee_id,
            status,
            evidence_note,
            confirmed_by,
            comment,
            valid_from,
            valid_until,
        ),
    )

def _ru(hex_codes):
    return "".join(chr(int(x, 16)) for x in hex_codes.split())

RU_DESCRIPTION = _ru(
    "0421 0438 043d 0442 0435 0442 0438 0447 0435 0441 043a 0430 044f "
    "0020 "
    "0442 0435 0445 043d 0438 0447 0435 0441 043a 0430 044f "
    "0020 "
    "0440 043e 043b 044c 002e 0020 "
    "0422 0440 0435 0431 0443 0435 0442 0020 "
    "043f 0440 043e 0432 0435 0440 043a 0438 002e"
)

ROLE_TITLES = {
    "HEAD_ORGANIZATION": _ru(
        "0420 0443 043a 043e 0432 043e 0434 0438 0442 0435 043b 044c "
        "0020 "
        "043e 0440 0433 0430 043d 0438 0437 0430 0446 0438 0438"
    ),
    "DEPUTY_HEAD": _ru(
        "0417 0430 043c 0435 0441 0442 0438 0442 0435 043b 044c "
        "0020 "
        "0440 0443 043a 043e 0432 043e 0434 0438 0442 0435 043b 044f"
    ),
    "OT_RESPONSIBLE": _ru(
        "041e 0442 0432 0435 0442 0441 0442 0432 0435 043d 043d 044b 0439 "
        "0020 "
        "043f 043e 0020 "
        "043e 0445 0440 0430 043d 0435 "
        "0020 "
        "0442 0440 0443 0434 0430"
    ),
    "OT_COMMISSION_CHAIR": _ru(
        "041f 0440 0435 0434 0441 0435 0434 0430 0442 0435 043b 044c "
        "0020 "
        "043a 043e 043c 0438 0441 0441 0438 0438 "
        "0020 "
        "043f 043e 0020 "
        "043e 0445 0440 0430 043d 0435 "
        "0020 "
        "0442 0440 0443 0434 0430"
    ),
    "OT_COMMISSION_MEMBER": _ru(
        "0427 043b 0435 043d "
        "0020 "
        "043a 043e 043c 0438 0441 0441 0438 0438 "
        "0020 "
        "043f 043e 0020 "
        "043e 0445 0440 0430 043d 0435 "
        "0020 "
        "0442 0440 0443 0434 0430"
    ),
    "TRAINING_RESPONSIBLE": _ru(
        "041e 0442 0432 0435 0442 0441 0442 0432 0435 043d 043d 044b 0439 "
        "0020 "
        "0437 0430 0020 "
        "043e 0431 0443 0447 0435 043d 0438 0435 "
        "0020 "
        "043f 043e 0020 "
        "043e 0445 0440 0430 043d 0435 "
        "0020 "
        "0442 0440 0443 0434 0430"
    ),
    "BRIEFING_RESPONSIBLE": _ru(
        "041e 0442 0432 0435 0442 0441 0442 0432 0435 043d 043d 044b 0439 "
        "0020 "
        "0437 0430 0020 "
        "0438 043d 0441 0442 0440 0443 043a 0442 0430 0436 0438"
    ),
    "KNOWLEDGE_CHECK_COMMISSION_CHAIR": _ru(
        "041f 0440 0435 0434 0441 0435 0434 0430 0442 0435 043b 044c "
        "0020 "
        "043a 043e 043c 0438 0441 0441 0438 0438 "
        "0020 "
        "043f 043e 0020 "
        "043f 0440 043e 0432 0435 0440 043a 0435 "
        "0020 "
        "0437 043d 0430 043d 0438 0439"
    ),
    "MEDICAL_EXAM_RESPONSIBLE": _ru(
        "041e 0442 0432 0435 0442 0441 0442 0432 0435 043d 043d 044b 0439 "
        "0020 "
        "0437 0430 0020 "
        "043e 0440 0433 0430 043d 0438 0437 0430 0446 0438 044e "
        "0020 "
        "043c 0435 0434 0438 0446 0438 043d 0441 043a 0438 0445 "
        "0020 "
        "043e 0441 043c 043e 0442 0440 043e 0432"
    ),
    "PSYCHIATRIC_EXAM_RESPONSIBLE": _ru(
        "041e 0442 0432 0435 0442 0441 0442 0432 0435 043d 043d 044b 0439 "
        "0020 "
        "0437 0430 0020 "
        "043f 0441 0438 0445 0438 0430 0442 0440 0438 0447 0435 0441 043a 0438 0435 "
        "0020 "
        "043e 0441 0432 0438 0434 0435 0442 0435 043b 044c 0441 0442 0432 043e 0432 0430 043d 0438 044f"
    ),
    "PPE_RESPONSIBLE": _ru(
        "041e 0442 0432 0435 0442 0441 0442 0432 0435 043d 043d 044b 0439 "
        "0020 "
        "0437 0430 0020 "
        "0421 0418 0417"
    ),
    "SOUT_RESPONSIBLE": _ru(
        "041e 0442 0432 0435 0442 0441 0442 0432 0435 043d 043d 044b 0439 "
        "0020 "
        "0437 0430 0020 "
        "0421 041e 0423 0422"
    ),
    "RISK_ASSESSMENT_RESPONSIBLE": _ru(
        "041e 0442 0432 0435 0442 0441 0442 0432 0435 043d 043d 044b 0439 "
        "0020 "
        "0437 0430 0020 "
        "043e 0446 0435 043d 043a 0443 "
        "0020 "
        "0440 0438 0441 043a 043e 0432"
    ),
    "ELECTRICAL_RESPONSIBLE": _ru(
        "041e 0442 0432 0435 0442 0441 0442 0432 0435 043d 043d 044b 0439 "
        "0020 "
        "0437 0430 0020 "
        "044d 043b 0435 043a 0442 0440 043e 0431 0435 0437 043e 043f 0430 0441 043d 043e 0441 0442 044c"
    ),
}

def _seed_roles(conn: sqlite3.Connection) -> None:
    for code in ROLE_CODES:
        role_id = f"ROLE_{code}"
        conn.execute(
            """
            INSERT INTO responsibility_roles (
                role_id,
                code,
                title,
                topic,
                description,
                active
            ) VALUES (
                ?,
                ?,
                ?,
                'OT',
                ?,
                1
            )
            ON CONFLICT(role_id) DO UPDATE SET
                code = excluded.code,
                title = excluded.title,
                topic = excluded.topic,
                description = excluded.description,
                updated_at = datetime('now')
            """,
            (
                role_id,
                code,
                ROLE_TITLES.get(code, code),
                RU_DESCRIPTION,
            ),
        )
