import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

EVENT_TYPES = (
    "MEDICAL_EXAM",
    "PSYCHIATRIC_EXAM",
    "TRAINING",
    "BRIEFING",
    "KNOWLEDGE_CHECK",
    "OTHER",
)

STATUS_VALUES = (
    "OK",
    "DUE_SOON",
    "EXPIRED",
    "NO_DATA",
    "RESTRICTED",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS periodic_events (
    event_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(company_id),
    employee_id TEXT NOT NULL REFERENCES employees(employee_id),
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    event_type TEXT NOT NULL
        CHECK (event_type IN ('MEDICAL_EXAM','PSYCHIATRIC_EXAM','TRAINING','BRIEFING','KNOWLEDGE_CHECK','OTHER')),
    event_code TEXT NOT NULL DEFAULT '',
    performed_at TEXT,
    valid_until TEXT,
    interval_days INTEGER,
    result_code TEXT,
    restriction_flag INTEGER NOT NULL DEFAULT 0 CHECK (restriction_flag IN (0, 1)),
    reference_note TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (company_id, employee_id, event_type, event_code)
);
"""


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_periodic_schema(db_path: Optional[Path] = None) -> None:
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


def _parse_date(value) -> Optional[date]:
    if value is None:
        return None

    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    return date.fromisoformat(text)


def _parse_interval(value) -> Optional[int]:
    if value is None:
        return None

    if isinstance(value, int):
        interval = value
    else:
        text = str(value).strip()
        if not text:
            return None
        interval = int(text)

    if interval < 0:
        raise ValueError("interval_days cannot be negative")

    return interval


def compute_event_status(event: dict, today: Optional[date] = None) -> dict:
    if today is None:
        today = date.today()

    performed = _parse_date(event.get("performed_at"))
    valid = _parse_date(event.get("valid_until"))
    interval = _parse_interval(event.get("interval_days"))

    due_date = None

    if valid is not None:
        due_date = valid
    elif performed is not None and interval is not None:
        due_date = performed + timedelta(days=interval)

    if due_date is None:
        status = "NO_DATA"
    elif due_date < today:
        status = "EXPIRED"
    elif due_date <= today + timedelta(days=30):
        status = "DUE_SOON"
    else:
        status = "OK"

    if int(event.get("restriction_flag") or 0) == 1:
        status = "RESTRICTED"

    return {
        "due_date": due_date.isoformat() if due_date else None,
        "status": status,
    }


def upsert_event(
    conn: sqlite3.Connection,
    company_id: str,
    employee_id: str,
    event_type: str,
    event_code: str = "",
    performed_at=None,
    valid_until=None,
    interval_days=None,
    result_code: Optional[str] = None,
    restriction_flag: int = 0,
    reference_note: Optional[str] = None,
    note: Optional[str] = None,
) -> None:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"invalid event_type: {event_type}")

    employee_row = conn.execute(
        "SELECT company_id FROM employees WHERE employee_id = ?",
        (employee_id,),
    ).fetchone()

    if not employee_row:
        raise ValueError(f"employee not found: {employee_id}")

    if employee_row["company_id"] != company_id:
        raise ValueError(
            f"employee {employee_id} does not belong to company {company_id}"
        )

    performed_date = _parse_date(performed_at)
    valid_date = _parse_date(valid_until)
    interval_value = _parse_interval(interval_days)

    code = (event_code or "").strip()
    event_id = f"PE:{company_id}:{employee_id}:{event_type}:{code}"

    conn.execute(
        """
        INSERT INTO periodic_events (
            event_id,
            company_id,
            employee_id,
            topic,
            event_type,
            event_code,
            performed_at,
            valid_until,
            interval_days,
            result_code,
            restriction_flag,
            reference_note,
            note
        ) VALUES (
            ?,
            ?,
            ?,
            'OT',
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
        ON CONFLICT(event_id) DO UPDATE SET
            performed_at = excluded.performed_at,
            valid_until = excluded.valid_until,
            interval_days = excluded.interval_days,
            result_code = excluded.result_code,
            restriction_flag = excluded.restriction_flag,
            reference_note = excluded.reference_note,
            note = excluded.note,
            updated_at = datetime('now')
        """,
        (
            event_id,
            company_id,
            employee_id,
            event_type,
            code,
            performed_date.isoformat() if performed_date else None,
            valid_date.isoformat() if valid_date else None,
            interval_value,
            result_code,
            1 if restriction_flag else 0,
            reference_note,
            note,
        ),
    )


def list_events(
    conn: sqlite3.Connection,
    company_id: str,
    employee_id: Optional[str] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> list[dict]:
    employees = {
        row["employee_id"]: row["display_name"]
        for row in list_employees(conn, company_id)
    }

    rows = conn.execute(
        "SELECT * FROM periodic_events WHERE company_id = ?",
        (company_id,),
    ).fetchall()

    result = []

    for row in rows:
        event = dict(row)
        event["employee_display"] = employees.get(event["employee_id"], event["employee_id"])
        event.update(compute_event_status(event))

        if employee_id and event["employee_id"] != employee_id:
            continue

        if event_type and event_type != "ALL" and event["event_type"] != event_type:
            continue

        if status and status != "ALL" and event["status"] != status:
            continue

        if search:
            haystack = " ".join(
                str(event.get(field) or "")
                for field in (
                    "event_id",
                    "event_type",
                    "event_code",
                    "employee_id",
                    "employee_display",
                    "result_code",
                    "reference_note",
                    "note",
                    "status",
                    "due_date",
                )
            ).lower()

            if search.strip().lower() not in haystack:
                continue

        result.append(event)

    return result


def count_events_by_status(conn: sqlite3.Connection, company_id: str) -> dict:
    events = list_events(conn, company_id)

    result = {status: 0 for status in STATUS_VALUES}
    result["total"] = 0

    for event in events:
        result[event["status"]] += 1
        result["total"] += 1

    return result
