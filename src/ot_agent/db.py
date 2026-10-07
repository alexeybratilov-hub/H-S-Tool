from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ot_agent.config import load_app_settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = Path("00_SYS/ot_local_agent.sqlite")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    legal_name TEXT NOT NULL,
    short_name TEXT,
    inn TEXT,
    kpp TEXT,
    ogrn TEXT,
    legal_address TEXT,
    actual_address TEXT,
    phone TEXT,
    email TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    industry_code TEXT,
    headcount INTEGER,
    has_branches INTEGER NOT NULL DEFAULT 0,
    has_hazardous_production_facility INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS company_attributes (
    attribute_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    attribute_key TEXT NOT NULL,
    attribute_value TEXT,
    value_type TEXT NOT NULL DEFAULT 'string',
    source_ref TEXT,
    confidence REAL,
    status TEXT NOT NULL DEFAULT 'USER_VERIFIED',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    UNIQUE (company_id, attribute_key)
);

CREATE TABLE IF NOT EXISTS departments (
    department_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    name TEXT NOT NULL,
    parent_department_id TEXT,
    responsible_employee_id TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_department_id) REFERENCES departments(department_id)
);

CREATE TABLE IF NOT EXISTS positions (
    position_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    title TEXT NOT NULL,
    department_id TEXT,
    headcount INTEGER,
    effective_from TEXT,
    effective_to TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    full_name TEXT NOT NULL,
    initials TEXT,
    personnel_number TEXT,
    position_id TEXT,
    department_id TEXT,
    hire_date TEXT,
    termination_date TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    comment TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    FOREIGN KEY (position_id) REFERENCES positions(position_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE INDEX IF NOT EXISTS idx_company_attributes_company_id
    ON company_attributes(company_id);

CREATE INDEX IF NOT EXISTS idx_departments_company_id
    ON departments(company_id);

CREATE INDEX IF NOT EXISTS idx_positions_company_id
    ON positions(company_id);

CREATE INDEX IF NOT EXISTS idx_employees_company_id
    ON employees(company_id);
"""


def resolve_db_path() -> Path:
    cfg = load_app_settings()
    paths = cfg.get("paths") if isinstance(cfg, dict) else None

    raw = None
    if isinstance(paths, dict):
        raw = paths.get("database")

    path = Path(raw) if raw else DEFAULT_DB_PATH

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _clean(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    return value


def _to_optional_int(value: Any) -> int | None:
    value = _clean(value)

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    return int(value)


def _to_bool_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)

    value = _clean(value)

    if value in (1, "1", "true", "True", "yes", "Yes", "да", "Да"):
        return 1

    return 0


@contextmanager
def connect():
    db_path = resolve_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def list_companies() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM companies
            ORDER BY legal_name
            """
        ).fetchall()

        return [dict(row) for row in rows]


def get_company(company_id: str) -> dict[str, Any] | None:
    company_id = _clean(company_id)

    if not company_id:
        return None

    with connect() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM companies
            WHERE company_id = ?
            """,
            (company_id,),
        ).fetchone()

        return dict(row) if row else None


def company_exists(company_id: str) -> bool:
    return get_company(company_id) is not None


def create_company(data: dict[str, Any]) -> dict[str, Any]:
    company_id = _clean(data.get("company_id"))
    legal_name = _clean(data.get("legal_name"))

    if not company_id:
        raise ValueError("Поле company_id обязательно.")

    if not legal_name:
        raise ValueError("Поле legal_name обязательно.")

    if company_exists(str(company_id)):
        raise ValueError(f"Компания с company_id={company_id} уже существует.")

    payload = (
        company_id,
        legal_name,
        _clean(data.get("short_name")),
        _clean(data.get("inn")),
        _clean(data.get("kpp")),
        _clean(data.get("ogrn")),
        _clean(data.get("legal_address")),
        _clean(data.get("actual_address")),
        _clean(data.get("phone")),
        _clean(data.get("email")),
        _clean(data.get("status")) or "ACTIVE",
        _clean(data.get("industry_code")),
        _to_optional_int(data.get("headcount")),
        _to_bool_int(data.get("has_branches")),
        _to_bool_int(data.get("has_hazardous_production_facility")),
    )

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO companies (
                company_id,
                legal_name,
                short_name,
                inn,
                kpp,
                ogrn,
                legal_address,
                actual_address,
                phone,
                email,
                status,
                industry_code,
                headcount,
                has_branches,
                has_hazardous_production_facility
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
        conn.commit()

    created = get_company(str(company_id))

    if created is None:
        raise RuntimeError("Компания создана, но не найдена в базе данных.")

    return created