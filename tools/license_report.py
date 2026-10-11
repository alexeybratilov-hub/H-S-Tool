#!/usr/bin/env python3
"""
License Report Tool for H-S-Tool

Generates license reports, checks for compliance, and validates dependencies.

Usage:
    python tools/license_report.py --check              # Check licenses (CI gate)
    python tools/license_report.py --output report.md # Generate full report
    python tools/license_report.py --format json      # JSON output
    python tools/license_report.py --generate-notice  # Generate NOTICE file

Color Scheme:
    Cyan   - Step headers, info
    Green  - PASS, OK, allowed
    Yellow - WARN, review required
    Red    - ERROR, FAIL, forbidden
    Magenta- Metrics, counts
    Gray   - Details
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# =============================================================================
# LICENSE DEFINITIONS
# =============================================================================

# Allowed licenses (permissive)
ALLOWED_LICENSES = {
    "MIT",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "Apache-2.0",
    "ISC",
    "Python-2.0",
    "Zlib",
    "Unlicense",
    "CC0-1.0",
    "0BSD",
    "BSD-1-Clause",
    "BSD-Zero-Clause",
    "WTFPL",
    "PostgreSQL",
}

# Licenses requiring review
REVIEW_REQUIRED_LICENSES = {
    "LGPL-2.1-only",
    "LGPL-3.0-only",
    "MPL-2.0",
    "EPL-1.0",
    "EPL-2.0",
    "CDDL-1.0",
    "AGPL-3.0",  # Actually forbidden, but included for detection
}

# Forbidden licenses
FORBIDDEN_LICENSES = {
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
    "SSPL-1.0",
    "BSL-1.1",
    "Commons Clause",
    "Non-commercial",
    "NC",
}


@dataclass
class Dependency:
    """Represents a Python dependency with license information."""
    name: str
    version: str
    license: Optional[str] = None
    license_source: str = "unknown"  # pip, pypi, manual, stdlib
    purpose: str = "runtime"  # runtime, dev, build, vendor
    purl: str = ""
    description: str = ""
    
    @property
    def status(self) -> str:
        """Determine license status."""
        if self.license is None:
            return "unknown"
        
        normalized = self.license.upper().replace(" ", "-").replace("-", "-")
        
        if normalized in {l.upper().replace(" ", "-") for l in ALLOWED_LICENSES}:
            return "allowed"
        elif normalized in {l.upper().replace(" ", "-") for l in FORBIDDEN_LICENSES}:
            return "forbidden"
        elif normalized in {l.upper().replace(" ", "-") for l in REVIEW_REQUIRED_LICENSES}:
            return "requires_review"
        else:
            return "unknown"
    
    @property
    def is_stdlib(self) -> bool:
        """Check if this is a Python standard library module."""
        return self.license_source == "stdlib"


@dataclass
class LicenseReport:
    """Complete license report."""
    timestamp: str
    dependencies: List[Dependency] = field(default_factory=list)
    
    @property
    def total_count(self) -> int:
        return len(self.dependencies)
    
    @property
    def runtime_deps(self) -> List[Dependency]:
        return [d for d in self.dependencies if d.purpose == "runtime" and not d.is_stdlib]
    
    @property
    def dev_deps(self) -> List[Dependency]:
        return [d for d in self.dependencies if d.purpose == "dev"]
    
    @property
    def allowed_count(self) -> int:
        return len([d for d in self.dependencies if d.status == "allowed"])
    
    @property
    def forbidden_count(self) -> int:
        return len([d for d in self.dependencies if d.status == "forbidden"])
    
    @property
    def unknown_count(self) -> int:
        return len([d for d in self.dependencies if d.status == "unknown"])
    
    @property
    def review_required_count(self) -> int:
        return len([d for d in self.dependencies if d.status == "requires_review"])
    
    @property
    def has_forbidden(self) -> bool:
        return self.forbidden_count > 0
    
    @property
    def has_unknown(self) -> bool:
        return self.unknown_count > 0
    
    @property
    def has_review_required(self) -> bool:
        return self.review_required_count > 0


# =============================================================================
# COLOR OUTPUT
# =============================================================================

class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    GRAY = "\033[90m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_step(message: str) -> None:
    """Print step header in cyan."""
    print(f"{Colors.CYAN}[STEP]{Colors.RESET} {message}")


def print_ok(message: str) -> None:
    """Print success message in green."""
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {message}")


def print_warn(message: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {message}")


def print_error(message: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {message}")


def print_metric(message: str) -> None:
    """Print metric in magenta."""
    print(f"{Colors.MAGENTA}[METRIC]{Colors.RESET} {message}")


def print_detail(message: str) -> None:
    """Print detail in gray."""
    print(f"{Colors.GRAY}{message}{Colors.RESET}")


# =============================================================================
# LICENSE DATABASE
# =============================================================================

# Known dependencies and their licenses (fallback when pip doesn't provide)
KNOWN_DEPENDENCIES: Dict[str, Dict[str, str]] = {
    "streamlit": {"license": "Apache-2.0", "purpose": "runtime"},
    "pandas": {"license": "BSD-3-Clause", "purpose": "runtime"},
    "numpy": {"license": "BSD-3-Clause", "purpose": "runtime"},
    "pdfplumber": {"license": "BSD-3-Clause", "purpose": "runtime"},
    "python-docx": {"license": "MIT", "purpose": "runtime"},
    "rich": {"license": "MIT", "purpose": "runtime"},
    "pydantic": {"license": "MIT", "purpose": "runtime"},
    "requests": {"license": "Apache-2.0", "purpose": "runtime"},
    "pytest": {"license": "MIT", "purpose": "dev"},
    "black": {"license": "MIT", "purpose": "dev"},
    "mypy": {"license": "MIT", "purpose": "dev"},
    "ruff": {"license": "MIT", "purpose": "dev"},
    "pip": {"license": "MIT", "purpose": "build"},
    "setuptools": {"license": "MIT", "purpose": "build"},
    "wheel": {"license": "MIT", "purpose": "build"},
}

# Standard library modules
STDLIB_MODULES = {
    "sqlite3",
    "json",
    "pathlib",
    "os",
    "sys",
    "datetime",
    "re",
    "hashlib",
    "argparse",
    "subprocess",
    "tempfile",
    "urllib",
    "http",
}


# =============================================================================
# DEPENDENCY SCANNING
# =============================================================================

def get_installed_dependencies() -> List[Dependency]:
    """Get list of installed Python dependencies with licenses."""
    deps = []
    
    try:
        # Get installed packages
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0 and result.stdout.strip():
            packages = json.loads(result.stdout)
            
            for pkg in packages:
                name = pkg.get("name", "").lower()
                version = pkg.get("version", "unknown")
                
                # Skip stdlib
                if name in STDLIB_MODULES:
                    deps.append(Dependency(
                        name=name,
                        version=version,
                        license="Python-2.0",
                        license_source="stdlib",
                        purpose="runtime",
                    ))
                    continue
                
                # Get license from pip
                license_info = get_pip_license(name)
                
                # Fallback to known dependencies
                if license_info is None and name in KNOWN_DEPENDENCIES:
                    info = KNOWN_DEPENDENCIES[name]
                    deps.append(Dependency(
                        name=name,
                        version=version,
                        license=info.get("license", "unknown"),
                        license_source="known_db",
                        purpose=info.get("purpose", "runtime"),
                    ))
                    continue
                
                # If still unknown, try to get from PyPI
                if license_info is None:
                    license_info = get_pypi_license(name)
                
                deps.append(Dependency(
                    name=name,
                    version=version,
                    license=license_info or "unknown",
                    license_source="pip" if license_info else "unknown",
                    purpose="runtime",
                ))
    except Exception as e:
        print_warn(f"Failed to scan dependencies: {e}")
    
    return deps


def get_pip_license(package_name: str) -> Optional[str]:
    """Get license from pip metadata."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.startswith("License:"):
                    license_str = line.split(":", 1)[1].strip()
                    if license_str and license_str != "UNKNOWN":
                        return license_str
    except Exception:
        pass
    
    return None


def get_pypi_license(package_name: str) -> Optional[str]:
    """Get license from PyPI (requires requests)."""
    try:
        import requests
        response = requests.get(
            f"https://pypi.org/pypi/{package_name}/json",
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            info = data.get("info", {})
            license_str = info.get("license", "")
            if license_str and license_str != "UNKNOWN":
                return license_str
    except Exception:
        pass
    
    return None


def scan_requirements_file(path: Path) -> List[Dependency]:
    """Scan a requirements file and extract dependencies."""
    deps = []
    
    if not path.exists():
        return deps
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Parse package name and version
            # Handle: package==1.0.0, package>=1.0.0, package[extra], etc.
            # Remove inline comments first
            clean_line = line.split("#")[0].strip()
            if not clean_line:
                continue
            # Extract package name (everything before first operator or bracket)
            pkg_name = clean_line.split("[")[0].split(">=")[0].split("==")[0].split("<=")[0].split("~=")[0].split("!")[0].strip()
            pkg_name = pkg_name.lower()
            
            # Skip if already processed
            if any(d.name.lower() == pkg_name for d in deps):
                continue
            
            # Get version if available
            if "==" in line:
                version = line.split("==")[1].split("[")[0].strip()
            else:
                version = "unknown"
            
            # Determine purpose based on filename
            if "dev" in path.name or "test" in path.name:
                purpose = "dev"
            elif "build" in path.name:
                purpose = "build"
            else:
                purpose = "runtime"
            
            # Get license from known database
            if pkg_name in KNOWN_DEPENDENCIES:
                info = KNOWN_DEPENDENCIES[pkg_name]
                deps.append(Dependency(
                    name=pkg_name,
                    version=version,
                    license=info.get("license", "unknown"),
                    license_source="known_db",
                    purpose=purpose,
                ))
            else:
                deps.append(Dependency(
                    name=pkg_name,
                    version=version,
                    license="unknown",
                    license_source="requirements",
                    purpose=purpose,
                ))
    
    return deps


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(
    deps: List[Dependency],
    output_format: str = "text",
    output_file: Optional[Path] = None,
    generate_notice: bool = False,
) -> Optional[str]:
    """Generate license report in specified format."""
    
    report = LicenseReport(
        timestamp=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        dependencies=deps,
    )
    
    if output_format == "json":
        return json.dumps(report_to_dict(report), indent=2, ensure_ascii=False)
    
    elif output_format == "text":
        text_report = generate_text_report(report)
        if output_file:
            output_file.write_text(text_report, encoding="utf-8")
        return text_report
    
    elif output_format == "markdown":
        md_report = generate_markdown_report(report)
        if output_file:
            output_file.write_text(md_report, encoding="utf-8")
        return md_report
    
    return None


def report_to_dict(report: LicenseReport) -> Dict:
    """Convert report to dictionary for JSON serialization."""
    return {
        "status": "FAIL" if report.has_forbidden else ("WARN" if report.has_unknown or report.has_review_required else "PASS"),
        "timestamp": report.timestamp,
        "summary": {
            "total": report.total_count,
            "runtime": len(report.runtime_deps),
            "dev": len(report.dev_deps),
            "allowed": report.allowed_count,
            "forbidden": report.forbidden_count,
            "unknown": report.unknown_count,
            "requires_review": report.review_required_count,
        },
        "dependencies": [
            {
                "name": d.name,
                "version": d.version,
                "license": d.license,
                "license_source": d.license_source,
                "purpose": d.purpose,
                "status": d.status,
                "is_stdlib": d.is_stdlib,
            }
            for d in report.dependencies
        ],
        "forbidden": [
            {
                "name": d.name,
                "version": d.version,
                "license": d.license,
            }
            for d in report.dependencies
            if d.status == "forbidden"
        ],
        "unknown": [
            {
                "name": d.name,
                "version": d.version,
            }
            for d in report.dependencies
            if d.status == "unknown"
        ],
        "requires_review": [
            {
                "name": d.name,
                "version": d.version,
                "license": d.license,
            }
            for d in report.dependencies
            if d.status == "requires_review"
        ],
    }


def generate_text_report(report: LicenseReport) -> str:
    """Generate human-readable text report."""
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("H-S-Tool License Report")
    lines.append("=" * 80)
    lines.append(f"Generated: {report.timestamp}")
    lines.append("")
    
    # Summary
    print_step("License Check Summary")
    
    if report.has_forbidden:
        print_error(f"Forbidden dependencies found: {report.forbidden_count}")
        lines.append(f"{Colors.RED}[ERROR]{Colors.RESET} Forbidden dependencies found: {report.forbidden_count}")
    else:
        print_ok("No forbidden dependencies")
        lines.append(f"{Colors.GREEN}[OK]{Colors.RESET} No forbidden dependencies")
    
    if report.has_unknown:
        print_warn(f"Unknown licenses: {report.unknown_count}")
        lines.append(f"{Colors.YELLOW}[WARN]{Colors.RESET} Unknown licenses: {report.unknown_count}")
    
    if report.has_review_required:
        print_warn(f"Dependencies requiring review: {report.review_required_count}")
        lines.append(f"{Colors.YELLOW}[WARN]{Colors.RESET} Dependencies requiring review: {report.review_required_count}")
    
    # Metrics
    print_metric(f"Total dependencies: {report.total_count}")
    print_metric(f"Runtime: {len(report.runtime_deps)}")
    print_metric(f"Dev: {len(report.dev_deps)}")
    print_metric(f"Allowed: {report.allowed_count}")
    
    lines.append(f"{Colors.MAGENTA}[METRIC]{Colors.RESET} Total dependencies: {report.total_count}")
    lines.append(f"{Colors.MAGENTA}[METRIC]{Colors.RESET} Runtime: {len(report.runtime_deps)}")
    lines.append(f"{Colors.MAGENTA}[METRIC]{Colors.RESET} Dev: {len(report.dev_deps)}")
    lines.append(f"{Colors.MAGENTA}[METRIC]{Colors.RESET} Allowed: {report.allowed_count}")
    lines.append("")
    
    # Details
    print_detail("Dependency Details:")
    lines.append(f"{Colors.GRAY}Dependency Details:{Colors.RESET}")
    lines.append("")
    
    for dep in sorted(report.dependencies, key=lambda d: d.name.lower()):
        if dep.is_stdlib:
            continue
        
        status_icon = {
            "allowed": f"{Colors.GREEN}✓{Colors.RESET}",
            "forbidden": f"{Colors.RED}✗{Colors.RESET}",
            "unknown": f"{Colors.YELLOW}?{Colors.RESET}",
            "requires_review": f"{Colors.YELLOW}⚠{Colors.RESET}",
        }.get(dep.status, " ")
        
        lines.append(f"  {status_icon} {dep.name:30} {dep.version:15} {dep.license or 'UNKNOWN':20} [{dep.purpose}]")
    
    lines.append("")
    
    # Forbidden list
    if report.forbidden_count > 0:
        print_error("Forbidden Dependencies:")
        lines.append(f"{Colors.RED}[ERROR] Forbidden Dependencies:{Colors.RESET}")
        for dep in report.dependencies:
            if dep.status == "forbidden":
                lines.append(f"  {Colors.RED}✗ {dep.name} ({dep.license}){Colors.RESET}")
        lines.append("")
    
    # Unknown list
    if report.unknown_count > 0:
        print_warn("Unknown Licenses:")
        lines.append(f"{Colors.YELLOW}[WARN] Unknown Licenses:{Colors.RESET}")
        for dep in report.dependencies:
            if dep.status == "unknown":
                lines.append(f"  {Colors.YELLOW}? {dep.name}{Colors.RESET}")
        lines.append("")
    
    # Review required list
    if report.review_required_count > 0:
        print_warn("Requires Review:")
        lines.append(f"{Colors.YELLOW}[WARN] Requires Review:{Colors.RESET}")
        for dep in report.dependencies:
            if dep.status == "requires_review":
                lines.append(f"  {Colors.YELLOW}⚠ {dep.name} ({dep.license}){Colors.RESET}")
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("Report Status: " + ("FAIL" if report.has_forbidden else ("WARN" if report.has_unknown or report.has_review_required else "PASS")))
    lines.append("=" * 80)
    
    return "\n".join(lines)


def generate_markdown_report(report: LicenseReport) -> str:
    """Generate markdown report."""
    lines = []
    
    lines.append("# H-S-Tool License Report")
    lines.append("")
    lines.append(f"**Generated:** {report.timestamp}")
    lines.append(f"**Status:** {'FAIL' if report.has_forbidden else ('WARN' if report.has_unknown or report.has_review_required else 'PASS')}")
    lines.append("")
    
    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Dependencies | {report.total_count} |")
    lines.append(f"| Runtime | {len(report.runtime_deps)} |")
    lines.append(f"| Dev | {len(report.dev_deps)} |")
    lines.append(f"| Allowed | {report.allowed_count} |")
    lines.append(f"| Forbidden | {report.forbidden_count} |")
    lines.append(f"| Unknown | {report.unknown_count} |")
    lines.append(f"| Requires Review | {report.review_required_count} |")
    lines.append("")
    
    # Status
    if report.has_forbidden:
        lines.append("## ❌ Forbidden Dependencies")
        lines.append("")
        lines.append("| Package | Version | License |")
        lines.append("|--------|---------|---------|")
        for dep in report.dependencies:
            if dep.status == "forbidden":
                lines.append(f"| {dep.name} | {dep.version} | {dep.license or 'UNKNOWN'} |")
        lines.append("")
    
    if report.has_unknown:
        lines.append("## ⚠️ Unknown Licenses")
        lines.append("")
        lines.append("| Package | Version |")
        lines.append("|--------|---------|")
        for dep in report.dependencies:
            if dep.status == "unknown":
                lines.append(f"| {dep.name} | {dep.version} |")
        lines.append("")
    
    if report.has_review_required:
        lines.append("## ⚠️ Requires Review")
        lines.append("")
        lines.append("| Package | Version | License |")
        lines.append("|--------|---------|---------|")
        for dep in report.dependencies:
            if dep.status == "requires_review":
                lines.append(f"| {dep.name} | {dep.version} | {dep.license or 'UNKNOWN'} |")
        lines.append("")
    
    # Full list
    lines.append("## All Dependencies")
    lines.append("")
    lines.append("| Package | Version | License | Status | Purpose |")
    lines.append("|--------|---------|---------|--------|---------|")
    for dep in sorted(report.dependencies, key=lambda d: d.name.lower()):
        if dep.is_stdlib:
            continue
        status_emoji = {
            "allowed": "✅",
            "forbidden": "❌",
            "unknown": "❓",
            "requires_review": "⚠️",
        }.get(dep.status, "")
        lines.append(f"| {dep.name} | {dep.version} | {dep.license or 'UNKNOWN'} | {status_emoji} | {dep.purpose} |")
    
    return "\n".join(lines)


def generate_notice_file(report: LicenseReport, output_path: Path) -> None:
    """Generate NOTICE file with attribution."""
    lines = []
    
    lines.append("=" * 80)
    lines.append("NOTICE FOR H-S-Tool")
    lines.append("=" * 80)
    lines.append("")
    lines.append("This product includes software developed by third parties.")
    lines.append("")
    lines.append("For complete license information, see docs/licensing/LICENSING_POLICY.md")
    lines.append("")
    lines.append("-" * 80)
    
    # Group by license
    licenses = {}
    for dep in report.dependencies:
        if dep.is_stdlib or dep.license is None:
            continue
        
        license_key = dep.license
        if license_key not in licenses:
            licenses[license_key] = []
        licenses[license_key].append(dep)
    
    for license_name in sorted(licenses.keys()):
        deps = licenses[license_name]
        lines.append(f"{license_name}")
        lines.append("-" * len(license_name))
        lines.append("")
        
        for dep in sorted(deps, key=lambda d: d.name.lower()):
            lines.append(f"  {dep.name} ({dep.version})")
        
        lines.append("")
    
    lines.append("=" * 80)
    
    output_path.write_text("\n".join(lines), encoding="utf-8")


# =============================================================================
# CHECK FUNCTION
# =============================================================================

def check_licenses(deps: List[Dependency]) -> Tuple[bool, List[str]]:
    """
    Check if all dependencies have allowed licenses.
    Returns (success, errors)
    """
    errors = []
    
    for dep in deps:
        if dep.is_stdlib:
            continue
        
        if dep.status == "forbidden":
            errors.append(f"Forbidden license: {dep.name} ({dep.license})")
        elif dep.status == "unknown":
            errors.append(f"Unknown license: {dep.name}")
        elif dep.status == "requires_review":
            errors.append(f"License requires review: {dep.name} ({dep.license})")
    
    return len(errors) == 0, errors


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="H-S-Tool License Report Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/license_report.py --check              Check licenses (CI gate)
  python tools/license_report.py --output report.md Generate full report
  python tools/license_report.py --format json      JSON output
  python tools/license_report.py --generate-notice  Generate NOTICE file
        """,
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check licenses only (for CI gate). Exit code 0=PASS, 1=FAIL.",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for report.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--generate-notice",
        action="store_true",
        help="Generate NOTICE file.",
    )
    parser.add_argument(
        "--requirements",
        type=str,
        help="Path to requirements file to scan.",
    )
    parser.add_argument(
        "--all-installed",
        action="store_true",
        help="Scan all installed packages (not recommended for CI).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable color output.",
    )
    
    args = parser.parse_args()
    
    # Disable colors if requested
    if args.no_color:
        Colors.CYAN = ""
        Colors.GREEN = ""
        Colors.YELLOW = ""
        Colors.RED = ""
        Colors.MAGENTA = ""
        Colors.GRAY = ""
        Colors.RESET = ""
    
    # Collect dependencies
    deps: List[Dependency] = []
    
    # By default, only scan requirements files
    # Scan requirements.txt
    default_req = Path("requirements.txt")
    if default_req.exists():
        print_step(f"Scanning {default_req}...")
        req_deps = scan_requirements_file(default_req)
        deps.extend(req_deps)
        print_metric(f"Found {len(req_deps)} requirements from {default_req}")
    
    # Scan requirements-dev.txt if exists
    dev_req = Path("requirements-dev.txt")
    if dev_req.exists():
        print_step(f"Scanning {dev_req}...")
        dev_deps = scan_requirements_file(dev_req)
        for dep in dev_deps:
            dep.purpose = "dev"
        deps.extend(dev_deps)
        print_metric(f"Found {len(dev_deps)} dev requirements")
    
    # Scan specified requirements file
    if args.requirements:
        req_path = Path(args.requirements)
        if req_path.exists():
            print_step(f"Scanning {req_path}...")
            req_deps = scan_requirements_file(req_path)
            deps.extend(req_deps)
            print_metric(f"Found {len(req_deps)} requirements from {req_path}")
    
    # Only scan installed if explicitly requested
    if args.all_installed:
        print_step("Scanning installed dependencies...")
        installed_deps = get_installed_dependencies()
        deps.extend(installed_deps)
        print_metric(f"Found {len(installed_deps)} installed packages")
    
    # Deduplicate
    seen = set()
    unique_deps = []
    for dep in deps:
        key = (dep.name.lower(), dep.version)
        if key not in seen:
            seen.add(key)
            unique_deps.append(dep)
    deps = unique_deps
    
    print_metric(f"Total unique dependencies: {len(deps)}")
    
    # Create report
    report = LicenseReport(
        timestamp=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        dependencies=deps,
    )
    
    # Check mode
    if args.check:
        success, errors = check_licenses(deps)
        
        if success:
            print_ok("License check PASSED")
            for dep in report.dependencies:
                if not dep.is_stdlib:
                    print_detail(f"  {Colors.GREEN}✓{Colors.RESET} {dep.name}: {dep.license or 'UNKNOWN'}")
            return 0
        else:
            print_error("License check FAILED")
            for error in errors:
                print_error(f"  {error}")
            return 1
    
    # Generate notice
    if args.generate_notice:
        notice_path = Path("third_party/NOTICES")
        notice_path.parent.mkdir(parents=True, exist_ok=True)
        generate_notice_file(report, notice_path)
        print_ok(f"NOTICE file generated: {notice_path}")
    
    # Generate report
    output = generate_report(
        deps=deps,
        output_format=args.format,
        output_file=Path(args.output) if args.output else None,
    )
    
    if output:
        print(output)
    
    # Return appropriate exit code
    if report.has_forbidden:
        return 1
    elif report.has_unknown or report.has_review_required:
        return 0  # WARN is not a failure for now
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
