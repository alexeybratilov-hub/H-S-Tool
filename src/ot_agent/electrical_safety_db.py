import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

EXPECTED_TABLES = (
    "electrical_group_catalog",
    "electrical_installations",
    "electrical_commissions",
    "commission_members",
    "knowledge_check_protocols",
    "protocol_items",
    "employee_electrical_qualifications",
    "electrical_permits",
)

COMPANY_TABLES = (
    "electrical_installations",
    "electrical_commissions",
    "commission_members",
    "knowledge_check_protocols",
    "protocol_items",
    "employee_electrical_qualifications",
    "electrical_permits",
)

SYNTHETIC_SOURCE_NOTE = "Synthetic technical seed. Requires verification."
SYNTHETIC_VALID_FROM = "2026-01-01"
SYNTHETIC_VALID_TO = "2026-12-31"

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS electrical_group_catalog (
        group_code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (status IN ('ACTIVE','INACTIVE','ARCHIVED')),
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
            CHECK (verification_status IN ('REQUIRES_VERIFICATION','VERIFIED','REJECTED')),
        source_note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS electrical_installations (
        installation_id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL REFERENCES companies(company_id),
        name TEXT NOT NULL,
        location TEXT,
        voltage_class_code TEXT,
        power_category_code TEXT,
        status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (status IN ('ACTIVE','INACTIVE','ARCHIVED','PLANNED')),
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
            CHECK (verification_status IN ('REQUIRES_VERIFICATION','VERIFIED','REJECTED')),
        source_note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS electrical_commissions (
        commission_id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL REFERENCES companies(company_id),
        name TEXT NOT NULL,
        valid_from TEXT,
        valid_to TEXT,
        status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (status IN ('ACTIVE','INACTIVE','ARCHIVED','PLANNED')),
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
            CHECK (verification_status IN ('REQUIRES_VERIFICATION','VERIFIED','REJECTED')),
        source_note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS commission_members (
        member_id TEXT PRIMARY KEY,
        commission_id TEXT NOT NULL REFERENCES electrical_commissions(commission_id),
        company_id TEXT NOT NULL REFERENCES companies(company_id),
        employee_id TEXT NOT NULL REFERENCES employees(employee_id),
        role_code TEXT NOT NULL DEFAULT 'MEMBER'
            CHECK (role_code IN ('CHAIRMAN','DEPUTY_CHAIRMAN','SECRETARY','MEMBER','EXAMINER','OBSERVER')),
        valid_from TEXT,
        valid_to TEXT,
        status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (status IN ('ACTIVE','INACTIVE','ARCHIVED','PLANNED')),
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
            CHECK (verification_status IN ('REQUIRES_VERIFICATION','VERIFIED','REJECTED')),
        source_note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (commission_id, employee_id, role_code)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS knowledge_check_protocols (
        protocol_id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL REFERENCES companies(company_id),
        commission_id TEXT REFERENCES electrical_commissions(commission_id),
        protocol_number TEXT,
        check_date TEXT,
        valid_to TEXT,
        status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (status IN ('ACTIVE','INACTIVE','ARCHIVED','PLANNED')),
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
            CHECK (verification_status IN ('REQUIRES_VERIFICATION','VERIFIED','REJECTED')),
        source_note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS protocol_items (
        item_id TEXT PRIMARY KEY,
        protocol_id TEXT NOT NULL REFERENCES knowledge_check_protocols(protocol_id),
        company_id TEXT NOT NULL REFERENCES companies(company_id),
        employee_id TEXT NOT NULL REFERENCES employees(employee_id),
        group_code TEXT NOT NULL REFERENCES electrical_group_catalog(group_code),
        result_code TEXT NOT NULL DEFAULT 'PASSED'
            CHECK (result_code IN ('PASSED','FAILED','PENDING','CANCELLED')),
        valid_to TEXT,
        note TEXT,
        status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (status IN ('ACTIVE','INACTIVE','ARCHIVED','PLANNED')),
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
            CHECK (verification_status IN ('REQUIRES_VERIFICATION','VERIFIED','REJECTED')),
        source_note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (protocol_id, employee_id, group_code)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS employee_electrical_qualifications (
        qualification_id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL REFERENCES companies(company_id),
        employee_id TEXT NOT NULL REFERENCES employees(employee_id),
        group_code TEXT NOT NULL REFERENCES electrical_group_catalog(group_code),
        valid_from TEXT,
        valid_to TEXT,
        protocol_id TEXT REFERENCES knowledge_check_protocols(protocol_id),
        status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (status IN ('ACTIVE','EXPIRED','REVOKED','PLANNED')),
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
            CHECK (verification_status IN ('REQUIRES_VERIFICATION','VERIFIED','REJECTED')),
        source_note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (company_id, employee_id, group_code, valid_from)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS electrical_permits (
        permit_id TEXT PRIMARY KEY,
        company_id TEXT NOT NULL REFERENCES companies(company_id),
        installation_id TEXT REFERENCES electrical_installations(installation_id),
        employee_id TEXT NOT NULL REFERENCES employees(employee_id),
        permit_type_code TEXT NOT NULL,
        issued_at TEXT,
        expires_at TEXT,
        status TEXT NOT NULL DEFAULT 'ACTIVE'
            CHECK (status IN ('ACTIVE','EXPIRED','REVOKED','PLANNED')),
        verification_status TEXT NOT NULL DEFAULT 'REQUIRES_VERIFICATION'
            CHECK (verification_status IN ('REQUIRES_VERIFICATION','VERIFIED','REJECTED')),
        source_note TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE (company_id, employee_id, permit_type_code, installation_id)
    );
    """,
]

CATALOG_GROUPS = (
    ("I", "Synthetic group I", "Technical synthetic group code. Verify against current rules."),
    ("II", "Synthetic group II", "Technical synthetic group code. Verify against current rules."),
    ("III", "Synthetic group III", "Technical synthetic group code. Verify against current rules."),
    ("IV", "Synthetic group IV", "Technical synthetic group code. Verify against current rules."),
    ("V", "Synthetic group V", "Technical synthetic group code. Verify against current rules."),
    ("UNKNOWN", "Unknown", "Placeholder for missing verification."),
)


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _count(conn: sqlite3.Connection, sql: str, params: Any = ()) -> int:
    row = conn.execute(sql, params).fetchone()
    return int(row[0] or 0) if row is not None else 0


def init_schema(conn: sqlite3.Connection) -> None:
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)


def seed_catalog(conn: sqlite3.Connection) -> int:
    inserted = 0

    for group_code, name, description in CATALOG_GROUPS:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO electrical_group_catalog (
                group_code,
                name,
                description,
                status,
                verification_status,
                source_note
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                group_code,
                name,
                description,
                "ACTIVE",
                "REQUIRES_VERIFICATION",
                SYNTHETIC_SOURCE_NOTE,
            ),
        )
        inserted += int(cur.rowcount or 0)

    return inserted


def seed_synthetic(conn: sqlite3.Connection) -> Dict[str, int]:
    init_schema(conn)

    stats: Dict[str, int] = {
        "catalog_inserted": 0,
        "installations_inserted": 0,
        "commissions_inserted": 0,
        "members_inserted": 0,
        "protocols_inserted": 0,
        "items_inserted": 0,
        "qualifications_inserted": 0,
        "permits_inserted": 0,
        "companies_seen": 0,
        "employees_seen": 0,
        "skipped_no_base_tables": 0,
    }

    stats["catalog_inserted"] = seed_catalog(conn)

    if not _table_exists(conn, "companies") or not _table_exists(conn, "employees"):
        stats["skipped_no_base_tables"] = 1
        return stats

    companies = [
        row[0]
        for row in conn.execute(
            "SELECT company_id FROM companies ORDER BY company_id"
        ).fetchall()
    ]

    stats["companies_seen"] = len(companies)

    if not companies:
        return stats

    group_cycle = ("I", "II", "III", "IV", "V")

    for company_id in companies:
        employees = [
            row[0]
            for row in conn.execute(
                """
                SELECT employee_id
                FROM employees
                WHERE company_id = ?
                ORDER BY employee_id
                """,
                (company_id,),
            ).fetchall()
        ]

        stats["employees_seen"] += len(employees)

        for seq in (1, 2):
            installation_id = f"ELEC_INST:{company_id}:{seq:03d}"

            cur = conn.execute(
                """
                INSERT OR IGNORE INTO electrical_installations (
                    installation_id,
                    company_id,
                    name,
                    location,
                    voltage_class_code,
                    power_category_code,
                    status,
                    verification_status,
                    source_note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    installation_id,
                    company_id,
                    f"Synthetic electrical installation {seq}",
                    f"Site {seq}",
                    "UNKNOWN",
                    "UNKNOWN",
                    "ACTIVE",
                    "REQUIRES_VERIFICATION",
                    SYNTHETIC_SOURCE_NOTE,
                ),
            )
            stats["installations_inserted"] += int(cur.rowcount or 0)

        commission_id = f"ELEC_COMM:{company_id}:MAIN"

        cur = conn.execute(
            """
            INSERT OR IGNORE INTO electrical_commissions (
                commission_id,
                company_id,
                name,
                valid_from,
                valid_to,
                status,
                verification_status,
                source_note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                commission_id,
                company_id,
                "Synthetic knowledge check commission",
                SYNTHETIC_VALID_FROM,
                SYNTHETIC_VALID_TO,
                "ACTIVE",
                "REQUIRES_VERIFICATION",
                SYNTHETIC_SOURCE_NOTE,
            ),
        )
        stats["commissions_inserted"] += int(cur.rowcount or 0)

        for role_code, employee_id in zip(
            ("CHAIRMAN", "SECRETARY", "MEMBER"),
            employees[:3],
        ):
            member_id = f"ELEC_MEM:{commission_id}:{employee_id}:{role_code}"

            cur = conn.execute(
                """
                INSERT OR IGNORE INTO commission_members (
                    member_id,
                    commission_id,
                    company_id,
                    employee_id,
                    role_code,
                    valid_from,
                    valid_to,
                    status,
                    verification_status,
                    source_note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    member_id,
                    commission_id,
                    company_id,
                    employee_id,
                    role_code,
                    SYNTHETIC_VALID_FROM,
                    SYNTHETIC_VALID_TO,
                    "ACTIVE",
                    "REQUIRES_VERIFICATION",
                    SYNTHETIC_SOURCE_NOTE,
                ),
            )
            stats["members_inserted"] += int(cur.rowcount or 0)

        protocol_id = f"ELEC_PROT:{company_id}:MAIN"

        cur = conn.execute(
            """
            INSERT OR IGNORE INTO knowledge_check_protocols (
                protocol_id,
                company_id,
                commission_id,
                protocol_number,
                check_date,
                valid_to,
                status,
                verification_status,
                source_note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                protocol_id,
                company_id,
                commission_id if employees else None,
                f"SYN-{company_id}-001",
                SYNTHETIC_VALID_FROM,
                SYNTHETIC_VALID_TO,
                "ACTIVE",
                "REQUIRES_VERIFICATION",
                SYNTHETIC_SOURCE_NOTE,
            ),
        )
        stats["protocols_inserted"] += int(cur.rowcount or 0)

        for idx, employee_id in enumerate(employees):
            group_code = group_cycle[idx % len(group_cycle)]

            qualification_id = f"ELEC_QUAL:{company_id}:{employee_id}:{group_code}"

            cur = conn.execute(
                """
                INSERT OR IGNORE INTO employee_electrical_qualifications (
                    qualification_id,
                    company_id,
                    employee_id,
                    group_code,
                    valid_from,
                    valid_to,
                    protocol_id,
                    status,
                    verification_status,
                    source_note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    qualification_id,
                    company_id,
                    employee_id,
                    group_code,
                    SYNTHETIC_VALID_FROM,
                    SYNTHETIC_VALID_TO,
                    protocol_id,
                    "ACTIVE",
                    "REQUIRES_VERIFICATION",
                    SYNTHETIC_SOURCE_NOTE,
                ),
            )
            stats["qualifications_inserted"] += int(cur.rowcount or 0)

            item_id = f"ELEC_PROTI:{protocol_id}:{employee_id}:{group_code}"

            cur = conn.execute(
                """
                INSERT OR IGNORE INTO protocol_items (
                    item_id,
                    protocol_id,
                    company_id,
                    employee_id,
                    group_code,
                    result_code,
                    valid_to,
                    note,
                    status,
                    verification_status,
                    source_note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    protocol_id,
                    company_id,
                    employee_id,
                    group_code,
                    "PASSED",
                    SYNTHETIC_VALID_TO,
                    "Synthetic protocol item.",
                    "ACTIVE",
                    "REQUIRES_VERIFICATION",
                    SYNTHETIC_SOURCE_NOTE,
                ),
            )
            stats["items_inserted"] += int(cur.rowcount or 0)

            if group_code in ("III", "IV", "V"):
                permit_id = f"ELEC_PERM:{company_id}:{employee_id}:OPERATIONAL"
                installation_id = f"ELEC_INST:{company_id}:001"

                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO electrical_permits (
                        permit_id,
                        company_id,
                        installation_id,
                        employee_id,
                        permit_type_code,
                        issued_at,
                        expires_at,
                        status,
                        verification_status,
                        source_note
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        permit_id,
                        company_id,
                        installation_id,
                        employee_id,
                        "OPERATIONAL",
                        SYNTHETIC_VALID_FROM,
                        SYNTHETIC_VALID_TO,
                        "ACTIVE",
                        "REQUIRES_VERIFICATION",
                        SYNTHETIC_SOURCE_NOTE,
                    ),
                )
                stats["permits_inserted"] += int(cur.rowcount or 0)

    return stats


def summary(conn: sqlite3.Connection) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    for table in EXPECTED_TABLES:
        if _table_exists(conn, table):
            out[table] = _count(conn, f"SELECT COUNT(*) FROM {table}")
        else:
            out[table] = "MISSING"

    return out


def validate_integrity(conn: sqlite3.Connection) -> List[str]:
    errors: List[str] = []

    for table in EXPECTED_TABLES:
        if not _table_exists(conn, table):
            errors.append("missing table: " + table)

    for table in ("companies", "employees"):
        if not _table_exists(conn, table):
            errors.append("missing base table: " + table)

    if errors:
        return errors

    catalog_rows = _count(conn, "SELECT COUNT(*) FROM electrical_group_catalog")

    if catalog_rows < 6:
        errors.append(f"electrical_group_catalog has too few rows: {catalog_rows}")

    for table in COMPANY_TABLES:
        orphan = _count(
            conn,
            f"""
            SELECT COUNT(*)
            FROM {table} t
            LEFT JOIN companies c ON c.company_id = t.company_id
            WHERE c.company_id IS NULL
            """,
        )

        if orphan:
            errors.append(f"{table} orphan company rows={orphan}")

    bad_qualifications = _count(
        conn,
        """
        SELECT COUNT(*)
        FROM employee_electrical_qualifications q
        LEFT JOIN employees e ON e.employee_id = q.employee_id
        WHERE e.employee_id IS NULL
           OR e.company_id <> q.company_id
        """,
    )

    if bad_qualifications:
        errors.append(f"employee_electrical_qualifications company/employee mismatch rows={bad_qualifications}")

    bad_qualification_protocols = _count(
        conn,
        """
        SELECT COUNT(*)
        FROM employee_electrical_qualifications q
        LEFT JOIN knowledge_check_protocols kp ON kp.protocol_id = q.protocol_id
        WHERE q.protocol_id IS NOT NULL
          AND (
            kp.protocol_id IS NULL
            OR kp.company_id <> q.company_id
          )
        """,
    )

    if bad_qualification_protocols:
        errors.append(f"employee_electrical_qualifications protocol mismatch rows={bad_qualification_protocols}")

    bad_members = _count(
        conn,
        """
        SELECT COUNT(*)
        FROM commission_members cm
        JOIN electrical_commissions ec ON ec.commission_id = cm.commission_id
        LEFT JOIN employees e ON e.employee_id = cm.employee_id
        WHERE e.employee_id IS NULL
           OR e.company_id <> cm.company_id
           OR cm.company_id <> ec.company_id
        """,
    )

    if bad_members:
        errors.append(f"commission_members company/employee mismatch rows={bad_members}")

    bad_protocol_items = _count(
        conn,
        """
        SELECT COUNT(*)
        FROM protocol_items pi
        JOIN knowledge_check_protocols kp ON kp.protocol_id = pi.protocol_id
        LEFT JOIN employees e ON e.employee_id = pi.employee_id
        WHERE e.employee_id IS NULL
           OR e.company_id <> pi.company_id
           OR pi.company_id <> kp.company_id
        """,
    )

    if bad_protocol_items:
        errors.append(f"protocol_items company/employee mismatch rows={bad_protocol_items}")

    bad_permits = _count(
        conn,
        """
        SELECT COUNT(*)
        FROM electrical_permits p
        LEFT JOIN employees e ON e.employee_id = p.employee_id
        LEFT JOIN electrical_installations ei ON ei.installation_id = p.installation_id
        WHERE e.employee_id IS NULL
           OR e.company_id <> p.company_id
           OR (
             p.installation_id IS NOT NULL
             AND (
               ei.installation_id IS NULL
               OR ei.company_id <> p.company_id
             )
           )
        """,
    )

    if bad_permits:
        errors.append(f"electrical_permits company/employee/installation mismatch rows={bad_permits}")

    return errors
