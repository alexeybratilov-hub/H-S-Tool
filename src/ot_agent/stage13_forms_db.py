import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

TABLE_CONFIG: Dict[str, Dict[str, Any]] = {
    "sout_campaigns": {
        "pk": "campaign_id",
        "company_col": "company_id",
        "display_cols": ["campaign_id", "title", "status", "verification_status"],
        "editable": [
            "status",
            "organization_name",
            "contract_number",
            "date_start",
            "date_end",
            "source_note",
            "verification_status",
        ],
        "required": ["status", "verification_status"],
        "numeric": [],
    },
    "sout_workplaces": {
        "pk": "workplace_id",
        "company_col": "company_id",
        "display_cols": ["workplace_id", "workplace_code", "title", "status"],
        "editable": [
            "status",
            "workplace_code",
            "title",
            "source_note",
            "verification_status",
        ],
        "required": ["status", "verification_status"],
        "numeric": [],
    },
    "ppe_norms": {
        "pk": "norm_id",
        "company_col": "company_id",
        "display_cols": ["norm_id", "item_id", "quantity", "status"],
        "editable": [
            "quantity",
            "unit",
            "validity_days",
            "status",
            "source_note",
            "verification_status",
        ],
        "required": ["status", "verification_status"],
        "numeric": ["quantity", "validity_days"],
    },
    "employee_ppe_cards": {
        "pk": "card_id",
        "company_col": "company_id",
        "display_cols": ["card_id", "employee_id", "status"],
        "editable": [
            "status",
            "note",
            "verification_status",
        ],
        "required": ["status", "verification_status"],
        "numeric": [],
    },
    "ppe_issue_records": {
        "pk": "record_id",
        "company_col": "company_id",
        "display_cols": ["record_id", "employee_id", "item_id", "issued_at"],
        "editable": [
            "quantity",
            "issued_at",
            "return_due_at",
            "status",
            "note",
        ],
        "required": ["status"],
        "numeric": ["quantity"],
    },
    "ppe_return_records": {
        "pk": "return_id",
        "company_col": "company_id",
        "display_cols": ["return_id", "employee_id", "item_id", "returned_at"],
        "editable": [
            "returned_at",
            "condition_code",
            "note",
        ],
        "required": [],
        "numeric": [],
    },
    "risk_register": {
        "pk": "risk_id",
        "company_col": "company_id",
        "display_cols": ["risk_id", "description", "risk_level_code", "status"],
        "editable": [
            "description",
            "likelihood_code",
            "severity_code",
            "risk_level_code",
            "control_measures",
            "status",
            "source_note",
            "verification_status",
        ],
        "required": ["status", "verification_status"],
        "numeric": [],
    },
}

EMPLOYEE_TABLES = {
    "employee_ppe_cards",
    "ppe_issue_records",
    "ppe_return_records",
}


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _cfg(table: str) -> Dict[str, Any]:
    try:
        return TABLE_CONFIG[table]
    except KeyError as exc:
        raise ValueError(f"unsupported table: {table}") from exc


def list_records(
    conn: sqlite3.Connection,
    table: str,
    company_id: str,
) -> List[Dict[str, Any]]:
    cfg = _cfg(table)
    cols = ", ".join(cfg["display_cols"])
    sql = (
        f"SELECT {cols} FROM {table} "
        f"WHERE {cfg['company_col']}=? "
        f"ORDER BY {cfg['pk']}"
    )
    cur = conn.execute(sql, (company_id,))
    names = [d[0] for d in cur.description]
    return [dict(zip(names, row)) for row in cur.fetchall()]


def get_record(
    conn: sqlite3.Connection,
    table: str,
    pk_value: str,
    company_id: str,
) -> Optional[Dict[str, Any]]:
    cfg = _cfg(table)
    cur = conn.execute(
        f"SELECT * FROM {table} WHERE {cfg['pk']}=? AND {cfg['company_col']}=?",
        (pk_value, company_id),
    )
    row = cur.fetchone()
    return dict(row) if row is not None else None


def _validate_employee_ownership(
    conn: sqlite3.Connection,
    table: str,
    record: Dict[str, Any],
) -> None:
    if table not in EMPLOYEE_TABLES:
        return

    employee_id = record.get("employee_id")
    if not employee_id:
        return

    row = conn.execute(
        "SELECT company_id FROM employees WHERE employee_id=?",
        (employee_id,),
    ).fetchone()

    if row is None or row[0] != record.get("company_id"):
        raise ValueError("employee does not belong to company")


def _coerce_numeric(field: str, value: Any) -> Optional[float]:
    if value is None:
        return None

    text = str(value).strip().replace(",", ".")
    if not text:
        return None

    try:
        number = float(text)
    except ValueError as exc:
        raise ValueError(f"invalid numeric value for {field}") from exc

    if field == "validity_days":
        if not number.is_integer():
            raise ValueError(f"{field} must be integer")
        return int(number)

    return number


def update_record(
    conn: sqlite3.Connection,
    table: str,
    pk_value: str,
    company_id: str,
    raw_values: Dict[str, Any],
) -> Dict[str, Any]:
    cfg = _cfg(table)
    allowed = set(cfg["editable"])
    required = set(cfg.get("required", ()))
    numeric = set(cfg.get("numeric", ()))

    changes: Dict[str, Any] = {}

    for key, value in raw_values.items():
        if key not in allowed:
            continue

        if isinstance(value, str):
            value = value.strip()

        if value == "":
            if key in required:
                continue
            changes[key] = None
        elif key in numeric:
            changes[key] = _coerce_numeric(key, value)
        else:
            changes[key] = value

    if not changes:
        raise ValueError("no allowed changes")

    record = get_record(conn, table, pk_value, company_id)
    if record is None:
        raise ValueError("record not found or company mismatch")

    _validate_employee_ownership(conn, table, record)

    set_parts = []
    params: List[Any] = []

    for key, value in changes.items():
        set_parts.append(f"{key}=?")
        params.append(value)

    params.extend([pk_value, company_id])

    sql = (
        f"UPDATE {table} SET {', '.join(set_parts)}, updated_at=datetime('now') "
        f"WHERE {cfg['pk']}=? AND {cfg['company_col']}=?"
    )

    try:
        cur = conn.execute(sql, params)
        if cur.rowcount != 1:
            conn.rollback()
            raise ValueError("update affected unexpected rows")
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return get_record(conn, table, pk_value, company_id)
