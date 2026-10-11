#!/usr/bin/env python3
"""
H-S-Tool Doctor - Unified Diagnostic Entry Point

A comprehensive diagnostic tool that integrates:
- System status checks (status_check.py)
- License compliance verification (license_report.py)
- SBOM generation and validation (sbom_generate.py)

This tool provides a single entry point for all diagnostic operations with
unified output formatting (colored text or JSON).

Usage:
    python tools/doctor.py                    # Run all checks with colored output
    python tools/doctor.py --format json     # Machine-readable JSON output
    python tools/doctor.py --no-color        # Plain text output
    python tools/doctor.py --check status     # Run only status checks
    python tools/doctor.py --check license    # Run only license checks
    python tools/doctor.py --check sbom       # Run only SBOM checks
    python tools/doctor.py --check all        # Run all checks (default)

Color Scheme (as per TZ Section 7):
    Cyan   - Step headers, informational messages
    Green  - PASS, OK, success, allowed
    Yellow - WARN, review required, optional feature disabled
    Red    - ERROR, FAIL, STOP, forbidden, violation
    Magenta- Metrics, counters, useful numbers
    Gray   - Details, secondary information

Exit Codes:
    0 - All checks passed (PASS)
    1 - Warnings detected (WARN)
    2 - Errors or failures detected (FAIL/ERROR)
    3 - Critical errors, cannot continue (STOP)
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


# =============================================================================
# COLOR SCHEME (ANSI Escape Codes) - TZ Section 7
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
# OUTPUT FORMAT
# =============================================================================

class OutputFormat:
    TEXT = "text"
    JSON = "json"


_current_format: str = OutputFormat.TEXT
_no_color_flag: bool = False


def set_output_format(fmt: str, no_color: bool = False) -> None:
    """Set the output format for the entire session."""
    global _current_format, _no_color_flag
    _current_format = fmt
    _no_color_flag = no_color


def _is_json_mode() -> bool:
    """Check if output should be JSON only."""
    return _current_format == OutputFormat.JSON


def _use_colors() -> bool:
    """Check if colors should be used (text format and not --no-color)."""
    return _current_format == OutputFormat.TEXT and not _no_color_flag


# =============================================================================
# OUTPUT FUNCTIONS - TZ Section 7 Color Scheme
# =============================================================================

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
    """Print a section header in Cyan."""
    if _is_json_mode():
        return
    if _use_colors():
        print(f"\n{Colors.CYAN}[{title}]{Colors.RESET}")
    else:
        print(f"\n[{title}]")


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class DoctorCheck:
    """A single diagnostic check result."""
    id: str
    category: str  # status, license, sbom
    status: str  # PASS, WARN, FAIL, ERROR, SKIP
    message: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}


@dataclass 
class DoctorReport:
    """Complete diagnostic report."""
    status: str  # PASS, WARN, FAIL, ERROR
    timestamp: str
    checks: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "system_info": self.system_info,
            "checks": self.checks,
            "summary": self.summary,
        }


# =============================================================================
# CHECK COLLECTOR
# =============================================================================

class CheckCollector:
    """Collects check results from all diagnostic modules."""

    def __init__(self):
        self.checks: List[DoctorCheck] = []
        self.system_info: Dict[str, Any] = {}

    def add_check(self, check_id: str, category: str, status: str, message: str,
                  metrics: Optional[Dict[str, Any]] = None,
                  details: Optional[str] = None) -> None:
        """Add a check result."""
        self.checks.append(DoctorCheck(
            id=check_id,
            category=category,
            status=status,
            message=message,
            metrics=metrics or {},
            details=details,
        ))

    def set_system_info(self, info: Dict[str, Any]) -> None:
        """Set system information."""
        self.system_info.update(info)

    def get_status(self) -> str:
        """Determine overall status from collected checks."""
        statuses = [c.status for c in self.checks]
        
        if "ERROR" in statuses:
            return "ERROR"
        if "FAIL" in statuses:
            return "FAIL"
        if "WARN" in statuses:
            return "WARN"
        return "PASS"

    def get_exit_code(self) -> int:
        """Get appropriate exit code based on status."""
        status = self.get_status()
        if status == "PASS":
            return 0
        elif status == "WARN":
            return 1
        elif status == "FAIL" or status == "ERROR":
            return 2
        return 3

    def get_report(self) -> DoctorReport:
        """Generate a complete report."""
        # Count by category and status
        categories: Dict[str, Dict[str, int]] = {}
        for check in self.checks:
            if check.category not in categories:
                categories[check.category] = {}
            if check.status not in categories[check.category]:
                categories[check.category][check.status] = 0
            categories[check.category][check.status] += 1

        # Flatten counts
        summary_counts = {}
        for category, statuses in categories.items():
            for status, count in statuses.items():
                summary_counts[f"{category}_{status.lower()}_count"] = count

        summary_counts["total_checks"] = len(self.checks)

        return DoctorReport(
            status=self.get_status(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            checks=[c.to_dict() for c in self.checks],
            summary=summary_counts,
            system_info=self.system_info,
        )


# Global collector instance
_collector = CheckCollector()


def get_collector() -> CheckCollector:
    """Get the global check collector."""
    return _collector


# =============================================================================
# STATUS CHECKS (from status_check.py functionality)
# =============================================================================

def run_status_checks() -> None:
    """Run system status checks."""
    collector = get_collector()
    
    print_header("SYSTEM_STATUS")

    # Python version check
    import sys as sys_module
    version = sys_module.version.split()[0]
    executable = sys_module.executable
    in_venv = getattr(sys_module, "base_prefix", None) != sys_module.prefix

    collector.set_system_info({
        "python_version": version,
        "python_executable": executable,
        "in_virtual_env": in_venv,
    })

    collector.add_check(
        "doctor.python.version",
        "status",
        "PASS",
        f"Python {version} detected",
        metrics={"version": version, "executable": executable}
    )
    print_ok(f"Python version: {version}")

    if in_venv:
        collector.add_check(
            "doctor.python.venv",
            "status",
            "PASS",
            "Virtual environment active"
        )
        print_ok("Virtual environment active")
    else:
        collector.add_check(
            "doctor.python.venv",
            "status",
            "WARN",
            "Not running in virtual environment"
        )
        print_warn("Not running in virtual environment")

    # Database check
    from pathlib import Path as PathLib
    ROOT = PathLib(__file__).resolve().parents[1]
    DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

    collector.add_check(
        "doctor.db.path",
        "status",
        "PASS",
        f"Database path: {DB_PATH}",
        metrics={"path": str(DB_PATH)}
    )
    print_detail(f"Database path: {DB_PATH}")

    if not DB_PATH.exists():
        collector.add_check(
            "doctor.db.exists",
            "status",
            "FAIL",
            "Database file missing",
            metrics={"path": str(DB_PATH)}
        )
        print_error("Database missing")
        return

    collector.add_check(
        "doctor.db.exists",
        "status",
        "PASS",
        "Database exists",
        metrics={"path": str(DB_PATH)}
    )
    print_ok("Database exists")

    # Check database tables
    import sqlite3
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Core tables
        core_tables = [
            "companies",
            "departments",
            "positions",
            "employees",
        ]
        
        for table in core_tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                collector.add_check(
                    f"doctor.db.table.{table}",
                    "status",
                    "PASS",
                    f"Table {table} has {count} rows",
                    metrics={"table": table, "count": count}
                )
                print_metric(f"{table}={count}")
            except sqlite3.Error:
                collector.add_check(
                    f"doctor.db.table.{table}",
                    "status",
                    "FAIL",
                    f"Table {table} missing or inaccessible"
                )
                print_error(f"{table}=MISSING")

    finally:
        if conn:
            conn.close()

    # Run full status_check.py integration
    print_step("Running detailed status checks...")
    try:
        # Import the check functions
        from status_check import _stage13_final_check, _stage14_electrical_check
        
        # Always capture output from status_check to avoid double printing
        import io
        import contextlib
        
        # Run Stage 13 and 14 checks with output suppressed
        # The results are collected via the global collector
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                # Set the output format for status_check to match doctor
                from status_check import set_output_format as sc_set_format, OutputFormat as SC_OutputFormat
                sc_set_format(OutputFormat.JSON if _is_json_mode() else OutputFormat.TEXT)
                _stage13_final_check()
            except Exception as e:
                collector.add_check(
                    "doctor.stage13.integration",
                    "status",
                    "ERROR",
                    f"Stage 13 check failed: {e}"
                )
                print_error(f"Stage 13 check failed: {e}")
            
            try:
                _stage14_electrical_check()
            except Exception as e:
                collector.add_check(
                    "doctor.stage14.integration",
                    "status",
                    "ERROR",
                    f"Stage 14 check failed: {e}"
                )
                print_error(f"Stage 14 check failed: {e}")

    except ImportError as e:
        collector.add_check(
            "doctor.status_check.import",
            "status",
            "WARN",
            f"Could not import status_check functions: {e}"
        )
        print_warn(f"Could not import status_check functions: {e}")
    except Exception as e:
        collector.add_check(
            "doctor.status_check.runtime",
            "status",
            "ERROR",
            f"Error running status checks: {e}"
        )
        print_error(f"Error running status checks: {e}")


# =============================================================================
# LICENSE CHECKS (from license_report.py functionality)
# =============================================================================

def run_license_checks() -> None:
    """Run license compliance checks."""
    collector = get_collector()
    
    print_header("LICENSE_COMPLIANCE")

    # Import license definitions
    try:
        from license_report import (
            ALLOWED_LICENSES,
            FORBIDDEN_LICENSES,
            REVIEW_REQUIRED_LICENSES,
            KNOWN_DEPENDENCIES,
            get_installed_dependencies,
        )
    except ImportError as e:
        collector.add_check(
            "doctor.license.import",
            "license",
            "ERROR",
            f"Failed to import license_report: {e}"
        )
        print_error(f"Failed to import license_report: {e}")
        return

    # Check for requirements.txt
    ROOT = Path(__file__).resolve().parents[1]
    req_file = ROOT / "requirements.txt"
    
    if req_file.exists():
        collector.add_check(
            "doctor.license.requirements",
            "license",
            "PASS",
            "requirements.txt found",
            metrics={"path": str(req_file)}
        )
        print_ok("requirements.txt found")
    else:
        collector.add_check(
            "doctor.license.requirements",
            "license",
            "WARN",
            "requirements.txt not found"
        )
        print_warn("requirements.txt not found")

    # Check for pyproject.toml
    pyproject_file = ROOT / "pyproject.toml"
    if pyproject_file.exists():
        collector.add_check(
            "doctor.license.pyproject",
            "license",
            "PASS",
            "pyproject.toml found",
            metrics={"path": str(pyproject_file)}
        )
        print_ok("pyproject.toml found")
    else:
        collector.add_check(
            "doctor.license.pyproject",
            "license",
            "WARN",
            "pyproject.toml not found"
        )
        print_warn("pyproject.toml not found")

    # Check for LICENSE file
    license_file = ROOT / "LICENSE"
    if license_file.exists():
        collector.add_check(
            "doctor.license.file",
            "license",
            "PASS",
            "LICENSE file found",
            metrics={"path": str(license_file)}
        )
        print_ok("LICENSE file found")
    else:
        collector.add_check(
            "doctor.license.file",
            "license",
            "WARN",
            "LICENSE file not found"
        )
        print_warn("LICENSE file not found")

    # Check for NOTICE file
    notice_file = ROOT / "NOTICE"
    if notice_file.exists():
        collector.add_check(
            "doctor.license.notice",
            "license",
            "PASS",
            "NOTICE file found",
            metrics={"path": str(notice_file)}
        )
        print_ok("NOTICE file found")
    else:
        collector.add_check(
            "doctor.license.notice",
            "license",
            "WARN",
            "NOTICE file not found"
        )
        print_warn("NOTICE file not found")

    # Check dependencies
    try:
        deps = get_installed_dependencies()
        collector.add_check(
            "doctor.license.dependencies",
            "license",
            "PASS",
            f"Found {len(deps)} installed dependencies",
            metrics={"dependency_count": len(deps)}
        )
        print_metric(f"dependencies={len(deps)}")

        # Check for forbidden licenses
        forbidden_count = 0
        review_count = 0
        allowed_count = 0
        unknown_count = 0

        for dep in deps:
            if dep.license:
                normalized = dep.license.upper().replace(" ", "-")
                if normalized in {l.upper().replace(" ", "-") for l in FORBIDDEN_LICENSES}:
                    forbidden_count += 1
                    collector.add_check(
                        f"doctor.license.forbidden.{dep.name}",
                        "license",
                        "FAIL",
                        f"Forbidden license: {dep.license}",
                        metrics={"package": dep.name, "license": dep.license}
                    )
                elif normalized in {l.upper().replace(" ", "-") for l in REVIEW_REQUIRED_LICENSES}:
                    review_count += 1
                    collector.add_check(
                        f"doctor.license.review.{dep.name}",
                        "license",
                        "WARN",
                        f"Review required: {dep.license}",
                        metrics={"package": dep.name, "license": dep.license}
                    )
                elif normalized in {l.upper().replace(" ", "-") for l in ALLOWED_LICENSES}:
                    allowed_count += 1
                else:
                    unknown_count += 1
                    collector.add_check(
                        f"doctor.license.unknown.{dep.name}",
                        "license",
                        "WARN",
                        f"Unknown license: {dep.license}",
                        metrics={"package": dep.name, "license": dep.license}
                    )

        print_metric(f"license_allowed={allowed_count}")
        if forbidden_count > 0:
            print_error(f"Forbidden licenses: {forbidden_count}")
        if review_count > 0:
            print_warn(f"Review required: {review_count}")
        if unknown_count > 0:
            print_warn(f"Unknown licenses: {unknown_count}")

    except Exception as e:
        collector.add_check(
            "doctor.license.scan",
            "license",
            "ERROR",
            f"Failed to scan dependencies: {e}"
        )
        print_error(f"Failed to scan dependencies: {e}")


# =============================================================================
# SBOM CHECKS (from sbom_generate.py functionality)
# =============================================================================

def run_sbom_checks() -> None:
    """Run SBOM generation and validation checks."""
    collector = get_collector()
    
    print_header("SBOM_VALIDATION")

    ROOT = Path(__file__).resolve().parents[1]

    # Check for SBOM directory
    sbom_dir = ROOT / "sbom"
    if sbom_dir.exists() and sbom_dir.is_dir():
        collector.add_check(
            "doctor.sbom.directory",
            "sbom",
            "PASS",
            "SBOM directory exists",
            metrics={"path": str(sbom_dir)}
        )
        print_ok("SBOM directory exists")
    else:
        collector.add_check(
            "doctor.sbom.directory",
            "sbom",
            "WARN",
            "SBOM directory not found"
        )
        print_warn("SBOM directory not found")

    # Check for CycloneDX SBOM
    cyclonedx_file = sbom_dir / "cyclonedx.json"
    if cyclonedx_file.exists():
        collector.add_check(
            "doctor.sbom.cyclonedx",
            "sbom",
            "PASS",
            "CycloneDX SBOM found",
            metrics={"path": str(cyclonedx_file)}
        )
        print_ok("CycloneDX SBOM found")
    else:
        collector.add_check(
            "doctor.sbom.cyclonedx",
            "sbom",
            "WARN",
            "CycloneDX SBOM not found"
        )
        print_warn("CycloneDX SBOM not found")

    # Check for SPDX SBOM
    spdx_file = sbom_dir / "spdx.json"
    if spdx_file.exists():
        collector.add_check(
            "doctor.sbom.spdx",
            "sbom",
            "PASS",
            "SPDX SBOM found",
            metrics={"path": str(spdx_file)}
        )
        print_ok("SPDX SBOM found")
    else:
        collector.add_check(
            "doctor.sbom.spdx",
            "sbom",
            "WARN",
            "SPDX SBOM not found"
        )
        print_warn("SPDX SBOM not found")

    # Check for third_party NOTICES
    third_party_dir = ROOT / "third_party"
    notices_file = third_party_dir / "NOTICES"
    if notices_file.exists():
        collector.add_check(
            "doctor.sbom.notices",
            "sbom",
            "PASS",
            "Third-party NOTICES found",
            metrics={"path": str(notices_file)}
        )
        print_ok("Third-party NOTICES found")
    else:
        collector.add_check(
            "doctor.sbom.notices",
            "sbom",
            "WARN",
            "Third-party NOTICES not found"
        )
        print_warn("Third-party NOTICES not found")

    # Try to generate SBOM if possible
    try:
        from sbom_generate import generate_cyclonedx, generate_spdx
        collector.add_check(
            "doctor.sbom.generator",
            "sbom",
            "PASS",
            "SBOM generator available"
        )
        print_ok("SBOM generator available")
    except ImportError:
        collector.add_check(
            "doctor.sbom.generator",
            "sbom",
            "WARN",
            "SBOM generator not available"
        )
        print_warn("SBOM generator not available")


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main() -> None:
    """Main entry point for doctor tool."""
    global _collector

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="H-S-Tool Doctor - Unified Diagnostic Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/doctor.py                    # Run all checks with colored output
  python tools/doctor.py --format json     # Machine-readable JSON output
  python tools/doctor.py --no-color        # Plain text output
  python tools/doctor.py --check status    # Run only status checks
  python tools/doctor.py --check license   # Run only license checks
  python tools/doctor.py --check sbom      # Run only SBOM checks
  python tools/doctor.py --check all       # Run all checks (default)

Exit Codes:
  0 - All checks passed (PASS)
  1 - Warnings detected (WARN)
  2 - Errors or failures detected (FAIL/ERROR)
  3 - Critical errors, cannot continue (STOP)
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
    parser.add_argument(
        "--check",
        choices=["all", "status", "license", "sbom"],
        default="all",
        help="Run specific checks: 'all' (default), 'status', 'license', 'sbom'"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path (for JSON format)"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress progress output (JSON mode only)"
    )

    args = parser.parse_args()

    # Initialize output format
    if args.no_color:
        set_output_format(OutputFormat.TEXT, no_color=True)
    else:
        set_output_format(args.format)

    # Initialize collector
    _collector = CheckCollector()

    # Print header (only in text mode)
    if not _is_json_mode():
        if _use_colors():
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print(f"{Colors.CYAN}  H-S-Tool Doctor - Unified Diagnostic Tool{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
            print()
        else:
            print("=" * 60)
            print("  H-S-Tool Doctor - Unified Diagnostic Tool")
            print("=" * 60)
            print()

    # Run selected checks
    if args.check in ["all", "status"]:
        run_status_checks()

    if args.check in ["all", "license"]:
        run_license_checks()

    if args.check in ["all", "sbom"]:
        run_sbom_checks()

    # Generate report
    collector = get_collector()
    report = collector.get_report()

    # Output results
    if _current_format == OutputFormat.JSON:
        # JSON output
        json_output = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_output)
            print_ok(f"Report saved to {args.output}")
        else:
            print(json_output)
    else:
        # Text output - print summary
        print_header("SUMMARY")
        
        status = collector.get_status()
        if status == "PASS":
            print_ok(f"ALL_CHECKS_{status}")
            print_detail("All diagnostic checks passed successfully.")
        elif status == "WARN":
            print_warn(f"ALL_CHECKS_{status}")
            print_detail("Some checks require attention but no critical issues found.")
        else:
            print_error(f"ALL_CHECKS_{status}")
            print_detail("Critical issues detected. Please review the errors above.")

    # Exit with appropriate code
    sys.exit(collector.get_exit_code())


if __name__ == "__main__":
    main()
