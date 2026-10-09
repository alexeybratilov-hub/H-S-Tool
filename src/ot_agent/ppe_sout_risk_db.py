import sqlite3
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

EXPECTED_TABLES = (
    "harmful_factors",
    "sout_campaigns",
    "sout_workplaces",
    "sout_results",
    "ppe_items",
    "ppe_norms",
    "employee_ppe_cards",
    "ppe_issue_records",
    "ppe_return_records",
    "risk_register",
)

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS harmful_factors (
        factor_id TEXT PRIMARY KEY,
        code TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        topic TEXT NOT NULL DEFAULT 'OT',
        description TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS sout_campaigns (
        campaign_id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        organization_name TEXT,
        contract_number TEXT,
        date_start TEXT,
        date_end TEXT,
        source_note TEXT,
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS sout_workplaces (
        workplace_id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL,
        department_id TEXT,
        position_id TEXT,
        employee_id TEXT,
        workplace_code TEXT,
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        source_note TEXT,
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS sout_results (
        result_id TEXT PRIMARY KEY,
        campaign_id TEXT,
        workplace_id TEXT NOT NULL,
        factor_id TEXT,
        class_code TEXT,
        class_title TEXT,
        measurement_value REAL,
        measurement_unit TEXT,
        source_chunk_id TEXT,
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS ppe_items (
        item_id TEXT PRIMARY KEY,
        code TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        topic TEXT NOT NULL DEFAULT 'OT',
        description TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS ppe_norms (
        norm_id TEXT PRIMARY KEY,
        company_id TEXT,
        position_id TEXT,
        factor_id TEXT,
        item_id TEXT NOT NULL,
        quantity REAL NOT NULL DEFAULT 1,
        unit TEXT,
        validity_days INTEGER,
        status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        source_note TEXT,
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS employee_ppe_cards (
        card_id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL,
        employee_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        note TEXT,
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,

    """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_employee_ppe_cards_company_employee
    ON employee_ppe_cards(company_id, employee_id);
    """,

    """
    CREATE TABLE IF NOT EXISTS ppe_issue_records (
        record_id TEXT PRIMARY KEY,
        card_id TEXT,
        company_id TEXT NOT NULL,
        employee_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        quantity REAL NOT NULL DEFAULT 1,
        issued_at TEXT,
        return_due_at TEXT,
        status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS ppe_return_records (
        return_id TEXT PRIMARY KEY,
        issue_record_id TEXT NOT NULL,
        company_id TEXT NOT NULL,
        employee_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        returned_at TEXT,
        condition_code TEXT,
        note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,

    """
    CREATE TABLE IF NOT EXISTS risk_register (
        risk_id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL,
        position_id TEXT,
        workplace_id TEXT,
        factor_id TEXT,
        description TEXT NOT NULL,
        likelihood_code TEXT,
        severity_code TEXT,
        risk_level_code TEXT,
        control_measures TEXT,
        status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        source_note TEXT,
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_sout_campaigns_company
    ON sout_campaigns(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_sout_workplaces_company
    ON sout_workplaces(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_sout_workplaces_position
    ON sout_workplaces(position_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_sout_results_workplace
    ON sout_results(workplace_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_sout_results_factor
    ON sout_results(factor_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_ppe_norms_company
    ON ppe_norms(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_ppe_norms_position
    ON ppe_norms(position_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_ppe_norms_item
    ON ppe_norms(item_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_employee_ppe_cards_company
    ON employee_ppe_cards(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_ppe_issue_records_company
    ON ppe_issue_records(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_ppe_issue_records_employee
    ON ppe_issue_records(employee_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_ppe_return_records_issue
    ON ppe_return_records(issue_record_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_risk_register_company
    ON risk_register(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_risk_register_position
    ON risk_register(position_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS ix_risk_register_factor
    ON risk_register(factor_id);
    """,
]


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema(db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()
        for statement in SCHEMA_STATEMENTS:
            cur.execute(statement)
        conn.commit()
    finally:
        conn.close()


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def count_table(conn: sqlite3.Connection, table_name: str) -> int:
    row = conn.execute("SELECT COUNT(*) FROM " + table_name).fetchone()
    return int(row[0])
