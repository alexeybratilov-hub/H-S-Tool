#!/usr/bin/env python
"""
OT Local Agent - System Status Check Tool

Provides comprehensive diagnostics for the H-S-Tool project including:
- Python environment verification
- Database integrity checks
- Stage 13 (document packaging) validation
- Stage 14 (electrical safety) validation
- Ollama LLM availability check

Supports both human-readable colored output and machine-readable JSON format.
"""

import argparse
import json
import sqlite3
import sys
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# COLOR SCHEME (ANSI Escape Codes)
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    GRAY = "\033[90m"
    WHITE = "\033[97m"
    RESET = "\033[0m"


# =============================================================================
# OUTPUT RENDERERS
# =============================================================================

class OutputFormat:
    """Output format constants."""
    TEXT = "text"
    JSON = "json"


@dataclass
class CheckResult:
    """Structured result of a single check."""
    id: str
    status: str  # PASS, WARN, FAIL, ERROR, SKIP
    message: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # Remove None values for cleaner JSON
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class CheckReport:
    """Complete check report."""
    status: str  # PASS, WARN, FAIL, ERROR
    timestamp: str
    checks: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "checks": self.checks,
            "summary": self.summary,
        }


# Global output format
_current_format: str = OutputFormat.TEXT


def set_output_format(fmt: str) -> None:
    """Set the output format for the entire session."""
    global _current_format
    _current_format = fmt


def _use_colors() -> bool:
    """Check if colors should be used (text format only)."""
    return _current_format == OutputFormat.TEXT


def _is_json_mode() -> bool:
    """Check if output should be JSON only."""
    return _current_format == OutputFormat.JSON


def print_step(message: str) -> None:
    """Print a step/section header in Cyan."""
    if _is_json_mode():
        return
    if _use_colors():
        print(f"{Colors.CYAN}[STEP] {message}{Colors.RESET}")
    else:
        print(f"[STEP] {message}")


def print_ok(message: str) -> None:
    """Print a success message in Green."""
    if _is_json_mode():
        return
    if _use_colors():
        print(f"{Colors.GREEN}[OK] {message}{Colors.RESET}")
    else:
        print(f"[OK] {message}")


def print_warn(message: str) -> None:
    """Print a warning message in Yellow."""
    if _is_json_mode():
        return
    if _use_colors():
        print(f"{Colors.YELLOW}[WARN] {message}{Colors.RESET}")
    else:
        print(f"[WARN] {message}")


def print_error(message: str) -> None:
    """Print an error message in Red."""
    if _is_json_mode():
        return
    if _use_colors():
        print(f"{Colors.RED}[ERROR] {message}{Colors.RESET}")
    else:
        print(f"[ERROR] {message}")


def print_metric(message: str) -> None:
    """Print a metric/counter in Magenta."""
    if _is_json_mode():
        return
    if _use_colors():
        print(f"{Colors.MAGENTA}[METRIC] {message}{Colors.RESET}")
    else:
        print(f"[METRIC] {message}")


def print_detail(message: str) -> None:
    """Print a detail message in Gray."""
    if _is_json_mode():
        return
    if _use_colors():
        print(f"{Colors.GRAY}[DETAIL] {message}{Colors.RESET}")
    else:
        print(f"[DETAIL] {message}")


def print_header(title: str) -> None:
    """Print a section header."""
    if _is_json_mode():
        return
    if _use_colors():
        print(f"\n{Colors.CYAN}[{title}]{Colors.RESET}")
    else:
        print(f"\n[{title}]")


# =============================================================================
# CHECK COLLECTOR (For JSON output)
# =============================================================================

class CheckCollector:
    """Collects check results for JSON output."""

    def __init__(self):
        self.checks: List[CheckResult] = []
        self.errors: List[str] = []

    def add_check(self, check_id: str, status: str, message: str, 
                  metrics: Optional[Dict[str, Any]] = None, 
                  details: Optional[str] = None) -> None:
        """Add a check result."""
        self.checks.append(CheckResult(
            id=check_id,
            status=status,
            message=message,
            metrics=metrics or {},
            details=details,
        ))

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def get_status(self) -> str:
        """Determine overall status from collected checks."""
        if self.errors:
            return "FAIL"
        
        statuses = [c.status for c in self.checks]
        if "FAIL" in statuses or "ERROR" in statuses:
            return "FAIL"
        if "WARN" in statuses:
            return "WARN"
        return "PASS"

    def get_report(self) -> CheckReport:
        """Generate a complete report."""
        return CheckReport(
            status=self.get_status(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            checks=[c.to_dict() for c in self.checks],
            summary={
                "total_checks": len(self.checks),
                "pass_count": sum(1 for c in self.checks if c.status == "PASS"),
                "warn_count": sum(1 for c in self.checks if c.status == "WARN"),
                "fail_count": sum(1 for c in self.checks if c.status == "FAIL"),
                "error_count": sum(1 for c in self.checks if c.status == "ERROR"),
                "error_count": len(self.errors),
            }
        )


# Global collector instance
_collector = CheckCollector()


def get_collector() -> CheckCollector:
    """Get the global check collector."""
    return _collector


# =============================================================================
# PATHS AND CONSTANTS
# =============================================================================

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"
OLLAMA_URL = "http://127.0.0.1:11434/api/tags"


def hr(title: str) -> None:
    """Print a horizontal rule with title. Legacy compatibility."""
    print_header(title)


# =============================================================================
# PYTHON ENVIRONMENT CHECKS
# =============================================================================

def check_python() -> List[CheckResult]:
    """Check Python environment and return structured results."""
    results = []
    collector = get_collector()

    print_header("PYTHON")

    # Check Python version
    version = sys.version.split()[0]
    executable = sys.executable
    in_venv = getattr(sys, "base_prefix", None) != sys.prefix

    print_detail(f"version={version}")
    print_detail(f"executable={executable}")
    print_detail(f"venv_active={in_venv}")

    # Structured checks
    check_id = "python.version"
    if version:
        collector.add_check(check_id, "PASS", f"Python {version} detected", 
                           metrics={"version": version, "executable": executable})
        print_ok(f"Python version: {version}")
    else:
        collector.add_check(check_id, "FAIL", "Python version not detected")
        print_error("Python version not detected")

    check_id = "python.venv"
    if in_venv:
        collector.add_check(check_id, "PASS", "Virtual environment active")
        print_ok("Virtual environment active")
    else:
        collector.add_check(check_id, "WARN", "Not running in virtual environment")
        print_warn("Not running in virtual environment")

    return results


# =============================================================================
# DATABASE CHECKS
# =============================================================================

def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    """Check if a table exists in the database."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


def count_table(conn: sqlite3.Connection, name: str) -> Optional[int]:
    """Count rows in a table."""
    if not table_exists(conn, name):
        return None

    try:
        return conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    except sqlite3.Error:
        return None


def check_db() -> None:
    """Check database integrity."""
    collector = get_collector()
    print_header("DATABASE")

    print_detail(f"path={DB_PATH}")

    # Check database exists
    check_id = "db.exists"
    if not DB_PATH.exists():
        collector.add_check(check_id, "FAIL", "Database file missing", 
                           metrics={"path": str(DB_PATH)})
        print_error(f"Database missing: {DB_PATH}")
        return

    collector.add_check(check_id, "PASS", "Database exists",
                       metrics={"path": str(DB_PATH)})
    print_ok("Database exists")

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)

        # Core tables to check
        tables = [
            "companies",
            "departments",
            "positions",
            "employees",
            "staffing_schedules",
            "staffing_schedule_rows",
            "job_descriptions",
            "regulatory_sources",
            "regulatory_chunks",
            "norm_applicability",
            "document_types",
            "baseline_documents",
        ]

        for table in tables:
            count = count_table(conn, table)
            check_id = f"db.table.{table}"
            
            if count is None:
                collector.add_check(check_id, "FAIL", f"Table {table} missing")
                print_error(f"{table}=MISSING_TABLE")
            else:
                collector.add_check(check_id, "PASS", f"Table {table} has {count} rows",
                                   metrics={"table": table, "count": count})
                print_metric(f"{table}={count}")

        # Check companies
        if table_exists(conn, "companies"):
            rows = conn.execute(
                "SELECT company_id FROM companies ORDER BY company_id LIMIT 10"
            ).fetchall()
            company_ids = [row[0] for row in rows]
            print_detail(f"company_ids={','.join(company_ids)}")
            collector.add_check("db.companies.list", "PASS", 
                               f"Found {len(company_ids)} companies",
                               metrics={"company_ids": company_ids, "count": len(company_ids)})

        # Check baseline documents status
        if table_exists(conn, "baseline_documents"):
            rows = conn.execute(
                """
                SELECT status, COUNT(*)
                FROM baseline_documents
                GROUP BY status
                ORDER BY status
                """
            ).fetchall()

            statuses = ";".join(f"{status}:{count}" for status, count in rows)
            print_detail(f"baseline_statuses={statuses}")
            collector.add_check("db.baseline_documents.status", "PASS",
                               "Baseline documents status checked",
                               metrics={"statuses": {s: c for s, c in rows}})

    finally:
        if conn:
            conn.close()


# =============================================================================
# OLLAMA CHECKS
# =============================================================================

def check_ollama() -> None:
    """Check Ollama LLM availability."""
    collector = get_collector()
    print_header("OLLAMA")

    check_id = "ollama.available"
    try:
        request = urllib.request.Request(OLLAMA_URL, method="GET")

        with urllib.request.urlopen(request, timeout=2) as response:
            data = json.load(response)

        models = data.get("models", [])
        names = []

        for model in models:
            name = model.get("name")
            if name:
                names.append(name)

        if names:
            collector.add_check(check_id, "PASS", f"Ollama running with {len(names)} models",
                               metrics={"model_count": len(names), "models": names[:5]})
            print_ok("Ollama is available")
            print_metric(f"models_count={len(names)}")
            if names:
                print_detail(f"models_sample={', '.join(names[:5])}")
        else:
            collector.add_check(check_id, "WARN", "Ollama running but no models loaded")
            print_warn("Ollama running but no models loaded")

    except Exception as exc:
        collector.add_check(check_id, "WARN", f"Ollama unavailable: {type(exc).__name__}",
                           details=str(exc))
        print_warn(f"Ollama unavailable: {type(exc).__name__}")
        print_detail(f"detail={type(exc).__name__}")
        print_detail("note=Ollama is optional for non-LLM interface checks")


# =============================================================================
# STAGE 13 CHECKS
# =============================================================================

def _stage13_final_check() -> None:
    """Perform Stage 13 final validation checks."""
    collector = get_collector()
    print_header("STAGE13_FINAL")

    import sqlite3
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    db = root / "00_SYS" / "ot_local_agent.sqlite"
    errors = []

    check_id_base = "stage13."

    if not db.exists():
        collector.add_check(f"{check_id_base}db.exists", "FAIL", "Database missing")
        print_error("Database missing")
        return

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    def table_exists(name):
        return cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone() is not None

    def columns(name):
        return {row[1] for row in cur.execute(f"PRAGMA table_info({name})").fetchall()}

    def count(sql, params=()):
        return int(cur.execute(sql, params).fetchone()[0] or 0)

    has_companies = table_exists("companies")
    if not has_companies:
        errors.append("companies_table_missing")
        collector.add_check(f"{check_id_base}companies.exists", "FAIL", "Companies table missing")

    # 1. stage13_package_suggestions
    check_id = f"{check_id_base}package_suggestions"
    if table_exists("stage13_package_suggestions"):
        cols = columns("stage13_package_suggestions")
        rows = count("SELECT COUNT(*) FROM stage13_package_suggestions")
        print_metric(f"stage13_package_suggestions_rows={rows}")
        collector.add_check(f"{check_id}.exists", "PASS", 
                           f"Package suggestions table has {rows} rows",
                           metrics={"row_count": rows})

        if rows <= 0:
            errors.append("stage13_package_suggestions_empty")
            collector.add_check(f"{check_id}.empty", "FAIL", "Package suggestions table is empty")

        if "status" in cols and "verification_status" in cols:
            bad = count(
                """
                SELECT COUNT(*)
                FROM stage13_package_suggestions
                WHERE status <> 'PRELIMINARY'
                   OR verification_status <> 'REQUIRES_VERIFICATION'
                """
            )
            print_metric(f"stage13_package_suggestions_bad_status_rows={bad}")
            if bad:
                errors.append("stage13_package_suggestions_bad_status")
                collector.add_check(f"{check_id}.status", "FAIL", 
                                   f"{bad} rows with bad status")
            else:
                collector.add_check(f"{check_id}.status", "PASS", "All statuses valid")

        if has_companies and "company_id" in cols:
            orphan = count(
                """
                SELECT COUNT(*)
                FROM stage13_package_suggestions
                WHERE company_id IS NULL
                   OR company_id NOT IN (SELECT company_id FROM companies)
                """
            )
            print_metric(f"stage13_package_suggestions_orphan_company_rows={orphan}")
            if orphan:
                errors.append("stage13_package_suggestions_orphan_company")
                collector.add_check(f"{check_id}.orphans", "FAIL", 
                                   f"{orphan} orphan company references")
            else:
                collector.add_check(f"{check_id}.orphans", "PASS", "No orphan company references")

        if "suggestion_id" in cols:
            dup = count(
                """
                SELECT COUNT(*)
                FROM (
                  SELECT suggestion_id
                  FROM stage13_package_suggestions
                  GROUP BY suggestion_id
                  HAVING COUNT(*) > 1
                )
                """
            )
            print_metric(f"stage13_package_suggestions_duplicate_ids={dup}")
            if dup:
                errors.append("stage13_package_suggestions_duplicate_ids")
                collector.add_check(f"{check_id}.duplicates", "FAIL", 
                                   f"{dup} duplicate suggestion IDs")
            else:
                collector.add_check(f"{check_id}.duplicates", "PASS", "No duplicate IDs")
    else:
        errors.append("stage13_package_suggestions_table_missing")
        collector.add_check(f"{check_id}.exists", "FAIL", "Package suggestions table missing")

    # 2. document_requirements STAGE13_PRELIMINARY
    check_id = f"{check_id_base}document_requirements"
    if table_exists("document_requirements"):
        cols = columns("document_requirements")

        if "source_type" in cols:
            rows = count(
                "SELECT COUNT(*) FROM document_requirements WHERE source_type = ?",
                ("STAGE13_PRELIMINARY",),
            )
            print_metric(f"stage13_requirement_rows={rows}")
            collector.add_check(f"{check_id}.count", "PASS", 
                               f"Found {rows} STAGE13_PRELIMINARY requirements",
                               metrics={"count": rows})

            if rows <= 0:
                errors.append("stage13_requirements_empty")
                collector.add_check(f"{check_id}.empty", "FAIL", "No STAGE13_PRELIMINARY requirements")

            if "status" in cols:
                for row in cur.execute(
                    """
                    SELECT status, COUNT(*) AS c
                    FROM document_requirements
                    WHERE source_type = ?
                    GROUP BY status
                    ORDER BY status
                    """,
                    ("STAGE13_PRELIMINARY",),
                ).fetchall():
                    print_metric(f"stage13_requirement_status_{row[0]}={row[1]}")

                bad_status = count(
                    """
                    SELECT COUNT(*)
                    FROM document_requirements
                    WHERE source_type = ?
                      AND status NOT IN ('CONFIRMED', 'REJECTED', 'REQUIRES_VERIFICATION')
                    """,
                    ("STAGE13_PRELIMINARY",),
                )
                print_metric(f"stage13_requirement_bad_status_rows={bad_status}")
                if bad_status:
                    errors.append("stage13_requirements_bad_status")
                    collector.add_check(f"{check_id}.status", "FAIL", 
                                       f"{bad_status} rows with invalid status")
                else:
                    collector.add_check(f"{check_id}.status", "PASS", "All requirement statuses valid")

            if has_companies and "company_id" in cols:
                orphan = count(
                    """
                    SELECT COUNT(*)
                    FROM document_requirements
                    WHERE source_type = ?
                      AND (
                        company_id IS NULL
                        OR company_id NOT IN (SELECT company_id FROM companies)
                      )
                    """,
                    ("STAGE13_PRELIMINARY",),
                )
                print_metric(f"stage13_requirement_orphan_company_rows={orphan}")
                if orphan:
                    errors.append("stage13_requirements_orphan_company")
                    collector.add_check(f"{check_id}.orphans", "FAIL", 
                                       f"{orphan} orphan company references")
                else:
                    collector.add_check(f"{check_id}.orphans", "PASS", "No orphan company references")

            if "requirement_id" in cols:
                dup = count(
                    """
                    SELECT COUNT(*)
                    FROM (
                      SELECT requirement_id
                      FROM document_requirements
                      WHERE source_type = ?
                      GROUP BY requirement_id
                      HAVING COUNT(*) > 1
                    )
                    """,
                    ("STAGE13_PRELIMINARY",),
                )
                print_metric(f"stage13_requirement_duplicate_ids={dup}")
                if dup:
                    errors.append("stage13_requirements_duplicate_ids")
                    collector.add_check(f"{check_id}.duplicates", "FAIL", 
                                       f"{dup} duplicate requirement IDs")
                else:
                    collector.add_check(f"{check_id}.duplicates", "PASS", "No duplicate requirement IDs")

            if "source_id" in cols:
                dup_source = count(
                    """
                    SELECT COUNT(*)
                    FROM (
                      SELECT company_id, source_id
                      FROM document_requirements
                      WHERE source_type = ?
                      GROUP BY company_id, source_id
                      HAVING COUNT(*) > 1
                    )
                    """,
                    ("STAGE13_PRELIMINARY",),
                )
                print_metric(f"stage13_requirement_duplicate_source_ids={dup_source}")
                if dup_source:
                    errors.append("stage13_requirements_duplicate_source_ids")
                    collector.add_check(f"{check_id}.duplicate_sources", "FAIL", 
                                       f"{dup_source} duplicate source IDs")
                else:
                    collector.add_check(f"{check_id}.duplicate_sources", "PASS", 
                                       "No duplicate source IDs")
        else:
            errors.append("document_requirements_source_type_missing")
            collector.add_check(f"{check_id}.schema", "FAIL", "Missing source_type column")
    else:
        errors.append("document_requirements_table_missing")
        collector.add_check(f"{check_id}.exists", "FAIL", "Document requirements table missing")

    # 3. technical packages PKG:S13_CONFIRMED:*
    check_id = f"{check_id_base}technical_packages"
    if table_exists("document_packages") and table_exists("package_items"):
        pkg_cols = columns("document_packages")
        item_cols = columns("package_items")

        if "package_id" not in pkg_cols or "company_id" not in pkg_cols:
            errors.append("document_packages_required_columns_missing")
            collector.add_check(f"{check_id}.schema", "FAIL", 
                               "Missing required columns in document_packages")
        if "package_id" not in item_cols or "requirement_id" not in item_cols:
            errors.append("package_items_required_columns_missing")
            collector.add_check(f"{check_id}.schema.items", "FAIL", 
                               "Missing required columns in package_items")

        if (
            "package_id" in pkg_cols
            and "company_id" in pkg_cols
            and "package_id" in item_cols
            and "requirement_id" in item_cols
        ):
            pkg_rows = count(
                "SELECT COUNT(*) FROM document_packages WHERE package_id LIKE ?",
                ("PKG:S13_CONFIRMED:%",),
            )
            print_metric(f"stage13_technical_packages={pkg_rows}")
            collector.add_check(f"{check_id}.count", "PASS", 
                               f"Found {pkg_rows} technical packages",
                               metrics={"package_count": pkg_rows})

            if has_companies:
                orphan_pkg = count(
                    """
                    SELECT COUNT(*)
                    FROM document_packages
                    WHERE package_id LIKE ?
                      AND (
                        company_id IS NULL
                        OR company_id NOT IN (SELECT company_id FROM companies)
                      )
                    """,
                    ("PKG:S13_CONFIRMED:%",),
                )
                print_metric(f"stage13_technical_package_orphan_company_rows={orphan_pkg}")
                if orphan_pkg:
                    errors.append("stage13_technical_packages_orphan_company")
                    collector.add_check(f"{check_id}.orphans", "FAIL", 
                                       f"{orphan_pkg} orphan packages")
                else:
                    collector.add_check(f"{check_id}.orphans", "PASS", "No orphan packages")

            item_rows = count(
                """
                SELECT COUNT(*)
                FROM package_items pi
                JOIN document_packages dp ON dp.package_id = pi.package_id
                WHERE dp.package_id LIKE ?
                """,
                ("PKG:S13_CONFIRMED:%",),
            )
            print_metric(f"stage13_technical_package_items={item_rows}")
            collector.add_check(f"{check_id}.items", "PASS", 
                               f"Found {item_rows} package items",
                               metrics={"item_count": item_rows})

            if table_exists("document_requirements"):
                req_cols = columns("document_requirements")

                if {
                    "requirement_id",
                    "company_id",
                    "source_type",
                    "status",
                }.issubset(req_cols):
                    invalid_items = count(
                        """
                        SELECT COUNT(*)
                        FROM package_items pi
                        JOIN document_packages dp ON dp.package_id = pi.package_id
                        LEFT JOIN document_requirements dr ON dr.requirement_id = pi.requirement_id
                        WHERE dp.package_id LIKE ?
                          AND (
                            dr.requirement_id IS NULL
                            OR dr.source_type <> 'STAGE13_PRELIMINARY'
                            OR dr.status <> 'CONFIRMED'
                            OR dr.company_id <> dp.company_id
                          )
                        """,
                        ("PKG:S13_CONFIRMED:%",),
                    )
                    print_metric(f"stage13_technical_package_invalid_items={invalid_items}")
                    if invalid_items:
                        errors.append("stage13_technical_package_invalid_items")
                        collector.add_check(f"{check_id}.invalid_items", "FAIL", 
                                           f"{invalid_items} invalid package items")
                    else:
                        collector.add_check(f"{check_id}.invalid_items", "PASS", 
                                           "No invalid package items")

                stale_packages = count(
                    """
                    SELECT COUNT(*)
                    FROM (
                      SELECT dp.package_id
                      FROM document_packages dp
                      LEFT JOIN package_items pi ON pi.package_id = dp.package_id
                      WHERE dp.package_id LIKE ?
                      GROUP BY dp.package_id
                      HAVING COUNT(pi.requirement_id) = 0
                    )
                    """,
                    ("PKG:S13_CONFIRMED:%",),
                )
                print_metric(f"stage13_technical_stale_packages={stale_packages}")
                if stale_packages:
                    errors.append("stage13_technical_stale_packages")
                    collector.add_check(f"{check_id}.stale", "FAIL", 
                                       f"{stale_packages} stale packages")
                else:
                    collector.add_check(f"{check_id}.stale", "PASS", "No stale packages")

                if table_exists("document_requirements"):
                    req_cols = columns("document_requirements")

                    if {
                        "company_id",
                        "source_type",
                        "status",
                    }.issubset(req_cols):
                        missing_packages = count(
                            """
                            SELECT COUNT(DISTINCT dr.company_id)
                            FROM document_requirements dr
                            WHERE dr.source_type = 'STAGE13_PRELIMINARY'
                              AND dr.status = 'CONFIRMED'
                              AND NOT EXISTS (
                                SELECT 1
                                FROM document_packages dp
                                WHERE dp.package_id = 'PKG:S13_CONFIRMED:' || dr.company_id
                              )
                            """
                        )
                        print_metric(f"stage13_missing_technical_packages={missing_packages}")
                        if missing_packages:
                            errors.append("stage13_missing_technical_packages")
                            collector.add_check(f"{check_id}.missing", "FAIL", 
                                               f"{missing_packages} companies missing packages")
                        else:
                            collector.add_check(f"{check_id}.missing", "PASS", 
                                               "All companies have packages")
    else:
        errors.append("document_packages_or_package_items_table_missing")
        collector.add_check(f"{check_id}.exists", "FAIL", 
                           "Document packages or package items table missing")

    # 4. controlled marker absence
    check_id = f"{check_id_base}controlled_marker"
    if table_exists("draft_versions"):
        dv_cols = columns("draft_versions")
        marker = "STAGE13_MANUAL_CHECK_20261009"
        conditions = []
        params = []

        if "content" in dv_cols:
            conditions.append("content LIKE ?")
            params.append("%" + marker + "%")

        if "author" in dv_cols:
            conditions.append("author = ?")
            params.append(marker)

        if "comment" in dv_cols:
            conditions.append("comment = ?")
            params.append(marker)

        if conditions:
            marker_count = count(
                "SELECT COUNT(*) FROM draft_versions WHERE " + " OR ".join(conditions),
                tuple(params),
            )
            print_metric(f"controlled_stage13_marker_versions={marker_count}")

            if marker_count != 0:
                errors.append("controlled_stage13_marker_present")
                collector.add_check(f"{check_id}", "FAIL", 
                                   f"Controlled marker found in {marker_count} versions")
            else:
                collector.add_check(f"{check_id}", "PASS", "Controlled marker not present")
        else:
            errors.append("draft_versions_marker_columns_missing")
            collector.add_check(f"{check_id}.schema", "FAIL", 
                               "Missing marker columns in draft_versions")
    else:
        errors.append("draft_versions_table_missing")
        collector.add_check(f"{check_id}.exists", "FAIL", "Draft versions table missing")

    if table_exists("drafts"):
        draft_cols = columns("drafts")

        if "title" in draft_cols:
            titled = count(
                "SELECT COUNT(*) FROM drafts WHERE title LIKE ?",
                ("Stage13 technical draft:%",),
            )
            print_metric(f"stage13_titled_drafts={titled}")
            collector.add_check(f"{check_id_base}drafts.titled", "PASS", 
                               f"Found {titled} Stage13 titled drafts",
                               metrics={"count": titled})

    conn.close()

    # Final Stage 13 status
    check_id = f"{check_id_base}final"
    if errors:
        collector.add_check(check_id, "FAIL", f"Stage 13 check failed with {len(errors)} errors",
                           details="; ".join(errors))
        print_error(f"STAGE13_FINAL_CHECK=FAIL ({len(errors)} errors)")
        for error in errors:
            print_error(f"STAGE13_FINAL_ERROR={error}")
    else:
        collector.add_check(check_id, "PASS", "Stage 13 check passed")
        print_ok("STAGE13_FINAL_CHECK=PASS")


# =============================================================================
# STAGE 14 (ELECTRICAL SAFETY) CHECKS
# =============================================================================

def _stage14_electrical_check() -> None:
    """Perform Stage 14 (electrical safety) validation checks."""
    collector = get_collector()
    print_header("ELECTRICAL")

    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    src_dir = root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    check_id_base = "electrical."

    try:
        from ot_agent.electrical_safety_db import get_connection, summary, validate_integrity
    except Exception as exc:
        collector.add_check(f"{check_id_base}import", "ERROR", 
                           f"Failed to import electrical_safety_db: {exc}")
        print_error(f"ELECTRICAL_CHECK=ERROR")
        print_error(f"ELECTRICAL_ERROR=import:{exc}")
        return

    conn = None
    try:
        conn = get_connection()
        snap = summary(conn)

        for table, value in sorted(snap.items()):
            check_id = f"{check_id_base}{table}"
            collector.add_check(check_id, "PASS", f"Table {table} has {value} rows",
                               metrics={"table": table, "count": value})
            print_metric(f"{table}={value}")

        errors = validate_integrity(conn)

        check_id = f"{check_id_base}integrity"
        if errors:
            collector.add_check(check_id, "FAIL", 
                               f"Electrical integrity check failed with {len(errors)} errors",
                               details="; ".join(errors[:50]))
            print_error("ELECTRICAL_CHECK=FAIL")
            for error in errors[:50]:
                print_error(f"ELECTRICAL_ERROR={error}")
        else:
            collector.add_check(check_id, "PASS", "Electrical integrity check passed")
            print_ok("ELECTRICAL_CHECK=PASS")
    except Exception as exc:
        collector.add_check(f"{check_id_base}runtime", "ERROR", 
                           f"Electrical check runtime error: {exc}")
        print_error("ELECTRICAL_CHECK=ERROR")
        print_error(f"ELECTRICAL_ERROR={exc}")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main() -> None:
    """Main entry point for status check tool."""
    global _collector

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="H-S-Tool System Status Check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/status_check.py              # Human-readable colored output
  python tools/status_check.py --format json  # Machine-readable JSON output
        """
    )
    parser.add_argument(
        "--format",
        choices=[OutputFormat.TEXT, OutputFormat.JSON],
        default=OutputFormat.TEXT,
        help="Output format: 'text' (default, colored) or 'json' (machine-readable)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output (implies --format text)"
    )

    args = parser.parse_args()

    # Initialize output format
    if args.no_color:
        set_output_format(OutputFormat.TEXT)
        # Disable colors by setting a flag
        # For now, we'll just not use color codes
        Colors.CYAN = ""
        Colors.GREEN = ""
        Colors.YELLOW = ""
        Colors.RED = ""
        Colors.MAGENTA = ""
        Colors.GRAY = ""
        Colors.RESET = ""
    else:
        set_output_format(args.format)

    # Initialize collector
    _collector = CheckCollector()

    # Print header (only in text mode)
    if not _is_json_mode():
        if _use_colors():
            print(f"{Colors.CYAN}OT_LOCAL_AGENT_STATUS_CHECK{Colors.RESET}")
            print(f"{Colors.GRAY}synthetic_only=true{Colors.RESET}")
        else:
            print("OT_LOCAL_AGENT_STATUS_CHECK")
            print("synthetic_only=true")

    # Run all checks
    check_python()
    check_db()
    check_ollama()

    # Run Stage 13 and 14 checks
    try:
        _stage13_final_check()
    except Exception as exc:
        collector = get_collector()
        collector.add_check("stage13.final", "ERROR", 
                           f"Stage 13 check failed: {exc}")
        print_error(f"STAGE13_FINAL_CHECK=ERROR")
        print_error(f"STAGE13_FINAL_ERROR={exc}")

    try:
        _stage14_electrical_check()
    except Exception as exc:
        collector = get_collector()
        collector.add_check("electrical.final", "ERROR", 
                           f"Stage 14 check failed: {exc}")
        print_error(f"ELECTRICAL_CHECK=ERROR")
        print_error(f"ELECTRICAL_ERROR={exc}")

    # Print summary
    print_header("SUMMARY")
    collector = get_collector()
    
    if _current_format == OutputFormat.JSON:
        # Output JSON report
        report = collector.get_report()
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        # Human-readable summary
        print_detail("If DATABASE status=MISSING, check 00_SYS/ot_local_agent.sqlite.")
        print_detail("If OLLAMA status=UNAVAILABLE, start or install Ollama only when LLM generation is needed.")
        
        # Print overall status
        overall_status = collector.get_status()
        if overall_status == "PASS":
            print_ok(f"ALL_CHECKS_{overall_status}")
        elif overall_status == "WARN":
            print_warn(f"ALL_CHECKS_{overall_status}")
        else:
            print_error(f"ALL_CHECKS_{overall_status}")


if __name__ == "__main__":
    main()
