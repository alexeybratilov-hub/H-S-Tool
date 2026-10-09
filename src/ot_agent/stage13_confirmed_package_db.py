import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

SOURCE_TYPE = "STAGE13_PRELIMINARY"
CONFIRMED_STATUS = "CONFIRMED"
PACKAGE_PREFIX = "PKG:S13_CONFIRMED:"
PACKAGE_NAME = "STAGE13_CONFIRMED_TECHNICAL"
PACKAGE_TOPIC = "OT"
PACKAGE_STATUS = "DRAFT"
PACKAGE_NOTE = "Technical Stage 13 confirmed package. Not legal confirmation."
ITEM_NOTE = "Technical confirmed Stage 13 preliminary requirement. Not legal confirmation."


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _columns(conn: sqlite3.Connection, table: str) -> Set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _require_columns(conn: sqlite3.Connection, table: str, required: Set[str]) -> List[str]:
    if not _table_exists(conn, table):
        return [f"missing table: {table}"]

    cols = _columns(conn, table)
    missing = sorted(required - cols)

    if missing:
        return [f"missing columns in {table}: " + ",".join(missing)]

    return []


def _insert_row(conn: sqlite3.Connection, table: str, values: Dict[str, Any]) -> None:
    cols = _columns(conn, table)
    filtered = {k: v for k, v in values.items() if k in cols}

    if not filtered:
        raise ValueError(f"no insertable columns for {table}")

    col_list = ", ".join(filtered.keys())
    placeholders = ", ".join(["?"] * len(filtered))
    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    conn.execute(sql, list(filtered.values()))


def package_id_for(company_id: str) -> str:
    return f"{PACKAGE_PREFIX}{company_id}"


def get_confirmed_requirements(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    issues = _require_columns(
        conn,
        "document_requirements",
        {"requirement_id", "company_id", "source_type", "status"},
    )

    if issues:
        return []

    rows = conn.execute(
        """
        SELECT requirement_id, company_id, code, title, status, source_type
        FROM document_requirements
        WHERE source_type = ?
          AND status = ?
        ORDER BY company_id, code, title, requirement_id
        """,
        (SOURCE_TYPE, CONFIRMED_STATUS),
    ).fetchall()

    return [dict(row) for row in rows]


def plan_sync(conn: sqlite3.Connection) -> Tuple[
    List[Dict[str, Any]],
    List[str],
    List[Tuple[str, str]],
    List[Dict[str, Any]],
    List[Tuple[str, str]],
    List[str],
]:
    issues: List[str] = []

    issues.extend(
        _require_columns(
            conn,
            "document_packages",
            {"package_id", "company_id"},
        )
    )

    issues.extend(
        _require_columns(
            conn,
            "package_items",
            {"package_id", "requirement_id"},
        )
    )

    if issues:
        return [], [], [], [], [], issues

    confirmed = get_confirmed_requirements(conn)
    confirmed_by_company: Dict[str, List[Dict[str, Any]]] = {}

    for row in confirmed:
        confirmed_by_company.setdefault(row["company_id"], []).append(row)

    companies_with_confirmed: Set[str] = set(confirmed_by_company.keys())

    existing_packages = [
        dict(row)
        for row in conn.execute(
            """
            SELECT package_id, company_id
            FROM document_packages
            WHERE package_id LIKE ?
            ORDER BY package_id
            """,
            (PACKAGE_PREFIX + "%",),
        ).fetchall()
    ]

    existing_package_ids = {pkg["package_id"] for pkg in existing_packages}

    existing_items = [
        dict(row)
        for row in conn.execute(
            """
            SELECT
                pi.package_id,
                pi.requirement_id,
                dp.company_id AS package_company_id,
                dr.company_id AS requirement_company_id,
                dr.source_type,
                dr.status
            FROM package_items pi
            JOIN document_packages dp ON dp.package_id = pi.package_id
            LEFT JOIN document_requirements dr ON dr.requirement_id = pi.requirement_id
            WHERE dp.package_id LIKE ?
            ORDER BY pi.package_id, pi.requirement_id
            """,
            (PACKAGE_PREFIX + "%",),
        ).fetchall()
    ]

    items_to_remove: List[Tuple[str, str]] = []
    kept_items_by_package: Dict[str, Set[str]] = {pkg: set() for pkg in existing_package_ids}

    for item in existing_items:
        pkg_id = item["package_id"]
        req_id = item["requirement_id"]

        valid = (
            item.get("source_type") == SOURCE_TYPE
            and item.get("status") == CONFIRMED_STATUS
            and item.get("requirement_company_id") is not None
            and item.get("requirement_company_id") == item.get("package_company_id")
        )

        if not valid:
            items_to_remove.append((pkg_id, req_id))
        else:
            kept_items_by_package.setdefault(pkg_id, set()).add(req_id)

    packages_to_create: List[Dict[str, Any]] = []
    packages_to_remove: List[str] = []
    items_to_add: List[Dict[str, Any]] = []

    now = _now()

    for pkg in existing_packages:
        if pkg["company_id"] not in companies_with_confirmed:
            packages_to_remove.append(pkg["package_id"])

    for company_id, reqs in confirmed_by_company.items():
        pkg_id = package_id_for(company_id)

        if pkg_id not in existing_package_ids:
            packages_to_create.append(
                {
                    "package_id": pkg_id,
                    "company_id": company_id,
                    "name": PACKAGE_NAME,
                    "topic": PACKAGE_TOPIC,
                    "status": PACKAGE_STATUS,
                    "note": PACKAGE_NOTE,
                    "created_at": now,
                    "updated_at": now,
                }
            )

        kept = kept_items_by_package.get(pkg_id, set())

        if "order_index" in _columns(conn, "package_items"):
            max_order = conn.execute(
                "SELECT COALESCE(MAX(order_index), 0) FROM package_items WHERE package_id = ?",
                (pkg_id,),
            ).fetchone()[0]
            next_order = int(max_order or 0) + 1
        else:
            next_order = 0

        for req in reqs:
            req_id = req["requirement_id"]

            if req_id in kept:
                continue

            item_values = {
                "package_id": pkg_id,
                "requirement_id": req_id,
                "order_index": next_order,
                "note": ITEM_NOTE,
                "created_at": now,
                "updated_at": now,
            }

            items_to_add.append(item_values)
            next_order += 1

    return (
        packages_to_create,
        packages_to_remove,
        items_to_add,
        items_to_remove,
        [row["requirement_id"] for row in confirmed],
        issues,
    )


def apply_sync(
    conn: sqlite3.Connection,
    packages_to_create: List[Dict[str, Any]],
    packages_to_remove: List[str],
    items_to_add: List[Dict[str, Any]],
    items_to_remove: List[Tuple[str, str]],
) -> Dict[str, int]:
    for pkg_id in packages_to_remove:
        conn.execute("DELETE FROM package_items WHERE package_id = ?", (pkg_id,))
        conn.execute("DELETE FROM document_packages WHERE package_id = ?", (pkg_id,))

    for pkg_id, req_id in items_to_remove:
        conn.execute(
            "DELETE FROM package_items WHERE package_id = ? AND requirement_id = ?",
            (pkg_id, req_id),
        )

    for values in packages_to_create:
        _insert_row(conn, "document_packages", values)

    for values in items_to_add:
        _insert_row(conn, "package_items", values)

    return {
        "packages_created": len(packages_to_create),
        "packages_removed": len(packages_to_remove),
        "items_added": len(items_to_add),
        "items_removed": len(items_to_remove),
    }


def validate_sync(conn: sqlite3.Connection) -> List[str]:
    errors: List[str] = []

    errors.extend(
        _require_columns(
            conn,
            "document_packages",
            {"package_id", "company_id"},
        )
    )

    errors.extend(
        _require_columns(
            conn,
            "package_items",
            {"package_id", "requirement_id"},
        )
    )

    errors.extend(
        _require_columns(
            conn,
            "document_requirements",
            {"requirement_id", "company_id", "source_type", "status"},
        )
    )

    if errors:
        return errors

    confirmed = get_confirmed_requirements(conn)
    confirmed_ids = {row["requirement_id"] for row in confirmed}
    confirmed_by_company: Dict[str, Set[str]] = {}

    for row in confirmed:
        confirmed_by_company.setdefault(row["company_id"], set()).add(row["requirement_id"])

    packages = [
        dict(row)
        for row in conn.execute(
            """
            SELECT package_id, company_id
            FROM document_packages
            WHERE package_id LIKE ?
            ORDER BY package_id
            """,
            (PACKAGE_PREFIX + "%",),
        ).fetchall()
    ]

    package_ids = {pkg["package_id"] for pkg in packages}
    package_company = {pkg["package_id"]: pkg["company_id"] for pkg in packages}

    for pkg in packages:
        company_exists = conn.execute(
            "SELECT 1 FROM companies WHERE company_id = ?",
            (pkg["company_id"],),
        ).fetchone()

        if company_exists is None:
            errors.append(f"package company missing: {pkg['package_id']}")

        if pkg["company_id"] not in confirmed_by_company:
            errors.append(f"stale technical package without confirmed requirements: {pkg['package_id']}")

    items = [
        dict(row)
        for row in conn.execute(
            """
            SELECT
                pi.package_id,
                pi.requirement_id,
                dp.company_id AS package_company_id,
                dr.company_id AS requirement_company_id,
                dr.source_type,
                dr.status
            FROM package_items pi
            JOIN document_packages dp ON dp.package_id = pi.package_id
            LEFT JOIN document_requirements dr ON dr.requirement_id = pi.requirement_id
            WHERE dp.package_id LIKE ?
            ORDER BY pi.package_id, pi.requirement_id
            """,
            (PACKAGE_PREFIX + "%",),
        ).fetchall()
    ]

    seen = set()

    for item in items:
        key = (item["package_id"], item["requirement_id"])

        if key in seen:
            errors.append(f"duplicate package item: {key[0]}|{key[1]}")

        seen.add(key)

        if item.get("source_type") != SOURCE_TYPE:
            errors.append(f"non-stage13 item in technical package: {item['package_id']}|{item['requirement_id']}")

        if item.get("status") != CONFIRMED_STATUS:
            errors.append(f"non-confirmed item in technical package: {item['package_id']}|{item['requirement_id']}")

        if item.get("requirement_company_id") != item.get("package_company_id"):
            errors.append(f"company mismatch in technical package item: {item['package_id']}|{item['requirement_id']}")

        if item["requirement_id"] not in confirmed_ids:
            errors.append(f"confirmed requirement missing from global confirmed set: {item['requirement_id']}")

    for company_id, req_ids in confirmed_by_company.items():
        pkg_id = package_id_for(company_id)

        if pkg_id not in package_ids:
            errors.append(f"missing technical package for confirmed company: {company_id}")
            continue

        package_item_req_ids = {
            item["requirement_id"]
            for item in items
            if item["package_id"] == pkg_id
        }

        missing = sorted(req_ids - package_item_req_ids)

        if missing:
            errors.append(
                f"confirmed requirements missing in {pkg_id}: " + ",".join(missing)
            )

    return errors


def summary(conn: sqlite3.Connection) -> Dict[str, Any]:
    confirmed = get_confirmed_requirements(conn)
    packages = conn.execute(
        "SELECT COUNT(*) FROM document_packages WHERE package_id LIKE ?",
        (PACKAGE_PREFIX + "%",),
    ).fetchone()[0]

    items = conn.execute(
        """
        SELECT COUNT(*)
        FROM package_items pi
        JOIN document_packages dp ON dp.package_id = pi.package_id
        WHERE dp.package_id LIKE ?
        """,
        (PACKAGE_PREFIX + "%",),
    ).fetchone()[0]

    return {
        "confirmed_requirements": len(confirmed),
        "technical_packages": packages,
        "technical_package_items": items,
    }
