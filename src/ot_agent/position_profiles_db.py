import sqlite3
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

PROFILE_STATUS_VALUES = ("DRAFT", "REQUIRES_VERIFICATION", "CONFIRMED", "REJECTED")
LINK_STATUS_VALUES = ("SUGGESTED", "CONFIRMED", "REJECTED", "REQUIRES_VERIFICATION")
LINK_TYPES = ("duty", "hazard", "work")

SCHEMA = """
CREATE TABLE IF NOT EXISTS duty_taxonomies (
    duty_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS hazard_taxonomies (
    hazard_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS work_types (
    work_type_id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT 'OT'
        CHECK (topic IN ('OT','FIRE','GO_CHS','INDUSTRIAL_SAFETY','ECOLOGY','OTHER')),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS position_profiles (
    profile_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(company_id),
    position_id TEXT NOT NULL REFERENCES positions(position_id),
    status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
        CHECK (status IN ('DRAFT','REQUIRES_VERIFICATION','CONFIRMED','REJECTED')),
    summary TEXT,
    source_note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (company_id, position_id)
);

CREATE TABLE IF NOT EXISTS position_duties (
    company_id TEXT NOT NULL REFERENCES companies(company_id),
    position_id TEXT NOT NULL REFERENCES positions(position_id),
    duty_id TEXT NOT NULL REFERENCES duty_taxonomies(duty_id),
    status TEXT NOT NULL DEFAULT 'SUGGESTED'
        CHECK (status IN ('SUGGESTED','CONFIRMED','REJECTED','REQUIRES_VERIFICATION')),
    source TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (company_id, position_id, duty_id)
);

CREATE TABLE IF NOT EXISTS position_hazards (
    company_id TEXT NOT NULL REFERENCES companies(company_id),
    position_id TEXT NOT NULL REFERENCES positions(position_id),
    hazard_id TEXT NOT NULL REFERENCES hazard_taxonomies(hazard_id),
    status TEXT NOT NULL DEFAULT 'SUGGESTED'
        CHECK (status IN ('SUGGESTED','CONFIRMED','REJECTED','REQUIRES_VERIFICATION')),
    source TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (company_id, position_id, hazard_id)
);

CREATE TABLE IF NOT EXISTS position_work_types (
    company_id TEXT NOT NULL REFERENCES companies(company_id),
    position_id TEXT NOT NULL REFERENCES positions(position_id),
    work_type_id TEXT NOT NULL REFERENCES work_types(work_type_id),
    status TEXT NOT NULL DEFAULT 'SUGGESTED'
        CHECK (status IN ('SUGGESTED','CONFIRMED','REJECTED','REQUIRES_VERIFICATION')),
    source TEXT,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (company_id, position_id, work_type_id)
);
"""

DUTY_ITEMS = [
    ("DUTY_OT_GENERAL", "General OT duties", "Synthetic duty taxonomy item."),
    ("DUTY_OT_INSTRUCTION", "Instruction-related duties", "Synthetic duty taxonomy item."),
    ("DUTY_OT_PPE", "PPE-related duties", "Synthetic duty taxonomy item."),
    ("DUTY_OT_MEDICAL", "Medical exam related duties", "Synthetic duty taxonomy item."),
    ("DUTY_OT_RISK", "Risk assessment related duties", "Synthetic duty taxonomy item."),
    ("DUTY_OT_TRAINING", "Training related duties", "Synthetic duty taxonomy item."),
]

HAZARD_ITEMS = [
    ("HAZ_OT_PHYSICAL", "Physical hazard", "Synthetic hazard taxonomy item."),
    ("HAZ_OT_CHEMICAL", "Chemical hazard", "Synthetic hazard taxonomy item."),
    ("HAZ_OT_BIOLOGICAL", "Biological hazard", "Synthetic hazard taxonomy item."),
    ("HAZ_OT_ERGONOMIC", "Ergonomic hazard", "Synthetic hazard taxonomy item."),
    ("HAZ_OT_PSYPHYSIOLOGICAL", "Psycho-physiological hazard", "Synthetic hazard taxonomy item."),
    ("HAZ_OT_ELECTRICAL", "Electrical hazard", "Synthetic hazard taxonomy item."),
]

WORK_ITEMS = [
    ("WT_OT_OFFICE", "Office work", "Synthetic work type item."),
    ("WT_OT_WAREHOUSE", "Warehouse work", "Synthetic work type item."),
    ("WT_OT_DRIVING", "Driving work", "Synthetic work type item."),
    ("WT_OT_HEIGHT", "Work at height", "Synthetic work type item."),
    ("WT_OT_ELECTRICAL", "Electrical work", "Synthetic work type item."),
    ("WT_OT_CONFINED", "Confined space work", "Synthetic work type item."),
]

TABLE_MAP = {
    "duty": ("position_duties", "duty_taxonomies", "duty_id"),
    "hazard": ("position_hazards", "hazard_taxonomies", "hazard_id"),
    "work": ("position_work_types", "work_types", "work_type_id"),
}


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _seed_taxonomies(conn: sqlite3.Connection) -> None:
    for code, title, description in DUTY_ITEMS:
        conn.execute(
            """
            INSERT INTO duty_taxonomies (duty_id, code, title, topic, description)
            VALUES (?, ?, ?, 'OT', ?)
            ON CONFLICT(duty_id) DO UPDATE SET
                code = excluded.code,
                title = excluded.title,
                description = excluded.description,
                updated_at = datetime('now')
            """,
            (code, code, title, description),
        )

    for code, title, description in HAZARD_ITEMS:
        conn.execute(
            """
            INSERT INTO hazard_taxonomies (hazard_id, code, title, topic, description)
            VALUES (?, ?, ?, 'OT', ?)
            ON CONFLICT(hazard_id) DO UPDATE SET
                code = excluded.code,
                title = excluded.title,
                description = excluded.description,
                updated_at = datetime('now')
            """,
            (code, code, title, description),
        )

    for code, title, description in WORK_ITEMS:
        conn.execute(
            """
            INSERT INTO work_types (work_type_id, code, title, topic, description)
            VALUES (?, ?, ?, 'OT', ?)
            ON CONFLICT(work_type_id) DO UPDATE SET
                code = excluded.code,
                title = excluded.title,
                description = excluded.description,
                updated_at = datetime('now')
            """,
            (code, code, title, description),
        )


def init_position_profiles_schema(db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        _seed_taxonomies(conn)
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


def _position_display_expr(conn: sqlite3.Connection) -> str:
    rows = conn.execute("PRAGMA table_info(positions)").fetchall()
    cols = {str(row[1]).lower(): row[1] for row in rows}

    candidates = [
        "title",
        "position_title",
        "name",
        "position_name",
        "code",
        "position_id",
    ]

    for candidate in candidates:
        if candidate in cols:
            return f"p.{cols[candidate]}"

    return "p.position_id"


def list_positions_for_company(conn: sqlite3.Connection, company_id: str) -> list[dict]:
    expr = _position_display_expr(conn)

    sql = f"""
        SELECT
            p.position_id,
            {expr} AS display_name
        FROM positions p
        WHERE p.company_id = ?
        ORDER BY display_name
    """

    try:
        rows = conn.execute(sql, (company_id,)).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError:
        return []


def list_duties(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT duty_id, code, title
        FROM duty_taxonomies
        WHERE topic = 'OT'
        ORDER BY code
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_hazards(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT hazard_id, code, title
        FROM hazard_taxonomies
        WHERE topic = 'OT'
        ORDER BY code
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_work_types(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT work_type_id, code, title
        FROM work_types
        WHERE topic = 'OT'
        ORDER BY code
        """
    ).fetchall()
    return [dict(row) for row in rows]


def ensure_profile(conn: sqlite3.Connection, company_id: str, position_id: str) -> None:
    profile_id = f"PP:{company_id}:{position_id}"

    conn.execute(
        """
        INSERT OR IGNORE INTO position_profiles (
            profile_id,
            company_id,
            position_id,
            status,
            source_note
        ) VALUES (
            ?,
            ?,
            ?,
            'REQUIRES_VERIFICATION',
            'synthetic'
        )
        """,
        (profile_id, company_id, position_id),
    )


def upsert_profile(
    conn: sqlite3.Connection,
    company_id: str,
    position_id: str,
    status: str,
    summary: Optional[str] = None,
    source_note: Optional[str] = None,
) -> None:
    if status not in PROFILE_STATUS_VALUES:
        raise ValueError(f"invalid profile status: {status}")

    profile_id = f"PP:{company_id}:{position_id}"

    conn.execute(
        """
        INSERT INTO position_profiles (
            profile_id,
            company_id,
            position_id,
            status,
            summary,
            source_note
        ) VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        ON CONFLICT(profile_id) DO UPDATE SET
            status = excluded.status,
            summary = excluded.summary,
            source_note = excluded.source_note,
            updated_at = datetime('now')
        """,
        (profile_id, company_id, position_id, status, summary, source_note),
    )


def _get_item_id(conn: sqlite3.Connection, link_type: str, code: str) -> Optional[str]:
    if link_type not in TABLE_MAP:
        raise ValueError(f"invalid link type: {link_type}")

    _, tax_table, id_col = TABLE_MAP[link_type]

    row = conn.execute(
        f"SELECT {id_col} FROM {tax_table} WHERE code = ?",
        (code,),
    ).fetchone()

    return row[id_col] if row else None


def upsert_link(
    conn: sqlite3.Connection,
    company_id: str,
    position_id: str,
    link_type: str,
    code: str,
    status: str,
    source: Optional[str] = None,
    note: Optional[str] = None,
) -> None:
    if link_type not in TABLE_MAP:
        raise ValueError(f"invalid link type: {link_type}")

    if status not in LINK_STATUS_VALUES:
        raise ValueError(f"invalid link status: {status}")

    position_row = conn.execute(
        "SELECT company_id FROM positions WHERE position_id = ?",
        (position_id,),
    ).fetchone()

    if not position_row:
        raise ValueError(f"position not found: {position_id}")

    if position_row["company_id"] != company_id:
        raise ValueError(
            f"position {position_id} does not belong to company {company_id}"
        )

    item_id = _get_item_id(conn, link_type, code)

    if not item_id:
        raise ValueError(f"{link_type} code not found: {code}")

    ensure_profile(conn, company_id, position_id)

    link_table, _, id_col = TABLE_MAP[link_type]

    conn.execute(
        f"""
        INSERT INTO {link_table} (
            company_id,
            position_id,
            {id_col},
            status,
            source,
            note
        ) VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        ON CONFLICT(company_id, position_id, {id_col}) DO UPDATE SET
            status = excluded.status,
            source = excluded.source,
            note = excluded.note,
            updated_at = datetime('now')
        """,
        (company_id, position_id, item_id, status, source, note),
    )


def list_profile_links(
    conn: sqlite3.Connection,
    company_id: str,
    position_id: str,
) -> list[dict]:
    sql = """
        SELECT * FROM (
            SELECT
                'duty' AS link_type,
                dt.code AS item_code,
                dt.title AS item_title,
                pd.status,
                pd.source,
                pd.note,
                pd.updated_at
            FROM position_duties pd
            JOIN duty_taxonomies dt ON pd.duty_id = dt.duty_id
            WHERE pd.company_id = ? AND pd.position_id = ?

            UNION ALL

            SELECT
                'hazard' AS link_type,
                ht.code AS item_code,
                ht.title AS item_title,
                ph.status,
                ph.source,
                ph.note,
                ph.updated_at
            FROM position_hazards ph
            JOIN hazard_taxonomies ht ON ph.hazard_id = ht.hazard_id
            WHERE ph.company_id = ? AND ph.position_id = ?

            UNION ALL

            SELECT
                'work' AS link_type,
                wt.code AS item_code,
                wt.title AS item_title,
                pw.status,
                pw.source,
                pw.note,
                pw.updated_at
            FROM position_work_types pw
            JOIN work_types wt ON pw.work_type_id = wt.work_type_id
            WHERE pw.company_id = ? AND pw.position_id = ?
        )
        ORDER BY link_type, item_code
    """

    rows = conn.execute(sql, (company_id, position_id, company_id, position_id, company_id, position_id)).fetchall()
    return [dict(row) for row in rows]
