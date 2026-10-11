#!/usr/bin/env python3
"""
SBOM (Software Bill of Materials) Generator for H-S-Tool

Generates CycloneDX and SPDX SBOMs for dependency tracking and compliance.

Usage:
    python tools/sbom_generate.py --format cyclonedx --output sbom/cyclonedx.json
    python tools/sbom_generate.py --format spdx --output sbom/spdx.json
    python tools/sbom_generate.py --validate
    python tools/sbom_generate.py --update

Color Scheme:
    Cyan   - Step headers, info
    Green  - PASS, OK, success
    Yellow - WARN, review required
    Red    - ERROR, FAIL
    Magenta- Metrics, counts
    Gray   - Details
"""

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

# Import from license_report for consistency
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from license_report import (
    ALLOWED_LICENSES,
    FORBIDDEN_LICENSES,
    REVIEW_REQUIRED_LICENSES,
    Dependency,
    KNOWN_DEPENDENCIES,
    STDLIB_MODULES,
    get_installed_dependencies,
    scan_requirements_file,
    Colors,
    print_step,
    print_ok,
    print_warn,
    print_error,
    print_metric,
    print_detail,
)


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
    RESET = "\033[0m"


def print_step(message: str) -> None:
    print(f"{Colors.CYAN}[STEP]{Colors.RESET} {message}")


def print_ok(message: str) -> None:
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {message}")


def print_warn(message: str) -> None:
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {message}")


def print_error(message: str) -> None:
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {message}")


def print_metric(message: str) -> None:
    print(f"{Colors.MAGENTA}[METRIC]{Colors.RESET} {message}")


# =============================================================================
# SBOM DATA MODELS
# =============================================================================

@dataclass
class SBOMComponent:
    """Represents a component in the SBOM."""
    name: str
    version: str
    type: str = "library"
    purl: str = ""
    description: str = ""
    licenses: List[str] = field(default_factory=list)
    license_concluded: Optional[str] = None
    license_declared: Optional[str] = None
    copyright: str = ""
    external_refs: List[Dict[str, str]] = field(default_factory=list)
    properties: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class CycloneDXSBOM:
    """CycloneDX 1.4 SBOM structure."""
    bom_format: str = "CycloneDX"
    spec_version: str = "1.4"
    serial_number: str = field(default_factory=lambda: f"urn:uuid:{uuid4()}")
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    components: List[SBOMComponent] = field(default_factory=list)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SPDXSBOM:
    """SPDX 2.3 SBOM structure."""
    spdx_version: str = "SPDX-2.3"
    data_license: str = "CC0-1.0"
    SPDXID: str = "SPDXRef-DOCUMENT"
    name: str = "H-S-Tool"
    document_namespace: str = field(default_factory=lambda: f"https://hstool.example/{uuid4()}")
    creation_info: Dict[str, Any] = field(default_factory=dict)
    packages: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, str]] = field(default_factory=list)


# =============================================================================
# PURL GENERATION
# =============================================================================

def generate_purl(name: str, version: str, ecosystem: str = "pypi") -> str:
    """Generate Package URL (purl) for a component."""
    # Normalize name
    safe_name = name.lower().replace("-", "-").replace("_", "-")
    safe_version = version.replace(" ", "")
    
    # Handle special cases
    if ecosystem == "pypi":
        return f"pkg:pypi/{safe_name}@{safe_version}"
    elif ecosystem == "stdlib":
        return f"pkg:python/{safe_name}"
    else:
        return f"pkg:{ecosystem}/{safe_name}@{safe_version}"


# =============================================================================
# LICENSE MAPPING
# =============================================================================

# SPDX license IDs mapping
SPDX_LICENSE_MAP: Dict[str, str] = {
    "MIT": "MIT",
    "BSD-2-Clause": "BSD-2-Clause",
    "BSD-3-Clause": "BSD-3-Clause",
    "Apache-2.0": "Apache-2.0",
    "ISC": "ISC",
    "Python-2.0": "Python-2.0",
    "Zlib": "Zlib",
    "Unlicense": "Unlicense",
    "CC0-1.0": "CC0-1.0",
    "GPL-2.0-only": "GPL-2.0-only",
    "GPL-3.0-only": "GPL-3.0-only",
    "LGPL-2.1-only": "LGPL-2.1-only",
    "LGPL-3.0-only": "LGPL-3.0-only",
    "MPL-2.0": "MPL-2.0",
    "AGPL-3.0-only": "AGPL-3.0-only",
}


def get_spdx_license(license_str: str) -> str:
    """Convert license string to SPDX ID."""
    if not license_str:
        return "NOASSERTION"
    
    # Normalize
    normalized = license_str.strip().upper().replace(" ", "-").replace("-", "-")
    
    # Direct match
    if normalized in SPDX_LICENSE_MAP:
        return SPDX_LICENSE_MAP[normalized]
    
    # Try to find closest match
    for spdx_id, spdx_name in SPDX_LICENSE_MAP.items():
        if spdx_name.upper().replace(" ", "-") == normalized:
            return spdx_id
    
    return "NOASSERTION"


# =============================================================================
# SBOM GENERATION
# =============================================================================

def generate_cyclonedx_sbom(
    deps: List[Dependency],
    project_name: str = "H-S-Tool",
    project_version: str = "1.0.0",
) -> CycloneDXSBOM:
    """Generate CycloneDX SBOM."""
    components = []
    
    for dep in deps:
        # Skip stdlib for SBOM (optional)
        if dep.is_stdlib:
            continue
        
        component = SBOMComponent(
            name=dep.name,
            version=dep.version,
            type="library",
            purl=generate_purl(dep.name, dep.version, "pypi"),
            description=KNOWN_DEPENDENCIES.get(dep.name, {}).get("description", ""),
            licenses=[get_spdx_license(dep.license or "")],
            license_concluded=get_spdx_license(dep.license or ""),
            license_declared=dep.license or "NOASSERTION",
            external_refs=[
                {
                    "type": "pypi",
                    "reference": f"{dep.name}/{dep.version}",
                }
            ],
            properties=[
                {"name": "hs_tool:purpose", "value": dep.purpose},
                {"name": "hs_tool:license_status", "value": dep.status},
                {"name": "hs_tool:license_source", "value": dep.license_source},
            ],
        )
        components.append(component)
    
    # Create SBOM
    sbom = CycloneDXSBOM(
        metadata={
            "component": {
                "type": "application",
                "bom-ref": f"{project_name}/{project_version}",
                "name": project_name,
                "version": project_version,
                "purl": f"pkg:hstool/{project_name}@{project_version}",
            },
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tools": [
                {
                    "vendor": "H-S-Tool",
                    "name": "sbom_generate.py",
                    "version": "1.0.0",
                }
            ],
        },
        components=components,
    )
    
    return sbom


def generate_spdx_sbom(
    deps: List[Dependency],
    project_name: str = "H-S-Tool",
    project_version: str = "1.0.0",
) -> SPDXSBOM:
    """Generate SPDX SBOM."""
    packages = []
    relationships = []
    
    # Document describes the project
    document_spdx_id = "SPDXRef-DOCUMENT"
    project_spdx_id = "SPDXRef-Project"
    
    # Add project package
    project_package = {
        "SPDXID": project_spdx_id,
        "name": project_name,
        "versionInfo": project_version,
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "copyrightText": "NOASSERTION",
        "externalRefs": [
            {
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "pypi",
                "referenceLocator": f"{project_name.lower()}/{project_version}",
            }
        ],
    }
    packages.append(project_package)
    
    # Add document relationship
    relationships.append({
        "spdxElementId": document_spdx_id,
        "relationshipType": "DESCRIBES",
        "relatedSpdxElement": project_spdx_id,
    })
    
    # Add dependencies
    for i, dep in enumerate(deps):
        if dep.is_stdlib:
            continue
        
        pkg_spdx_id = f"SPDXRef-Package-{i}"
        
        package = {
            "SPDXID": pkg_spdx_id,
            "name": dep.name,
            "versionInfo": dep.version,
            "downloadLocation": f"https://pypi.org/packages/{dep.name}/{dep.version}",
            "filesAnalyzed": False,
            "licenseConcluded": get_spdx_license(dep.license or ""),
            "licenseDeclared": dep.license or "NOASSERTION",
            "copyrightText": "NOASSERTION",
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "pypi",
                    "referenceLocator": f"{dep.name}/{dep.version}",
                }
            ],
            "annotation": f"Purpose: {dep.purpose}, Status: {dep.status}",
        }
        packages.append(package)
        
        # Add dependency relationship
        relationships.append({
            "spdxElementId": project_spdx_id,
            "relationshipType": "DEPENDS_ON",
            "relatedSpdxElement": pkg_spdx_id,
        })
    
    sbom = SPDXSBOM(
        name=project_name,
        document_namespace=f"https://hstool.example/{project_name}/{uuid4()}",
        creation_info={
            "created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "creators": [
                "Tool: sbom_generate.py-1.0.0",
            ],
        },
        packages=packages,
        relationships=relationships,
    )
    
    return sbom


# =============================================================================
# SBOM SERIALIZATION
# =============================================================================

def sbom_to_dict(sbom: Any) -> Dict[str, Any]:
    """Convert SBOM object to dictionary."""
    if isinstance(sbom, CycloneDXSBOM):
        return {
            "bomFormat": sbom.bom_format,
            "specVersion": sbom.spec_version,
            "serialNumber": sbom.serial_number,
            "version": sbom.version,
            "metadata": sbom.metadata,
            "components": [
                {
                    "type": c.type,
                    "bom-ref": f"{c.name}/{c.version}",
                    "name": c.name,
                    "version": c.version,
                    "purl": c.purl,
                    "description": c.description,
                    "licenses": c.licenses,
                    "licenseConcluded": c.license_concluded,
                    "licenseDeclared": c.license_declared,
                    "externalRefs": c.external_refs,
                    "properties": c.properties,
                }
                for c in sbom.components
            ],
        }
    elif isinstance(sbom, SPDXSBOM):
        return {
            "spdxVersion": sbom.spdx_version,
            "dataLicense": sbom.data_license,
            "SPDXID": sbom.SPDXID,
            "name": sbom.name,
            "documentNamespace": sbom.document_namespace,
            "creationInfo": sbom.creation_info,
            "packages": sbom.packages,
            "relationships": sbom.relationships,
        }
    else:
        return asdict(sbom)


# =============================================================================
# SBOM VALIDATION
# =============================================================================

def validate_sbom(sbom_path: Path) -> Tuple[bool, List[str]]:
    """Validate an SBOM file."""
    errors = []
    
    if not sbom_path.exists():
        errors.append(f"SBOM file not found: {sbom_path}")
        return False, errors
    
    try:
        with open(sbom_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Failed to read SBOM: {e}")
        return False, errors
    
    # Check required fields for CycloneDX
    if data.get("bomFormat") == "CycloneDX":
        required_fields = ["bomFormat", "specVersion", "components"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if "components" in data:
            for i, comp in enumerate(data["components"]):
                comp_errors = validate_cyclonedx_component(comp, i)
                errors.extend(comp_errors)
    
    # Check required fields for SPDX
    elif data.get("spdxVersion"):
        required_fields = ["spdxVersion", "name", "packages"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
    
    else:
        errors.append("Unknown SBOM format")
    
    return len(errors) == 0, errors


def validate_cyclonedx_component(comp: Dict[str, Any], index: int) -> List[str]:
    """Validate a CycloneDX component."""
    errors = []
    prefix = f"Component[{index}]"
    
    if "name" not in comp:
        errors.append(f"{prefix}: missing 'name'")
    if "version" not in comp:
        errors.append(f"{prefix}: missing 'version'")
    if "purl" not in comp:
        errors.append(f"{prefix}: missing 'purl'")
    
    return errors


# =============================================================================
# SBOM STORAGE
# =============================================================================

def save_sbom(sbom: Any, output_path: Path, format: str = "cyclonedx") -> None:
    """Save SBOM to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    sbom_dict = sbom_to_dict(sbom)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sbom_dict, f, indent=2, ensure_ascii=False)
    
    print_ok(f"SBOM saved to {output_path}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_project_version() -> str:
    """Get project version from various sources."""
    # Try pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        try:
            import tomllib
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                return data.get("project", {}).get("version", "1.0.0")
        except Exception:
            pass
    
    # Try __version__.py
    version_path = Path("src/hs_tool/__version__.py")
    if version_path.exists():
        try:
            with open(version_path, "r") as f:
                for line in f:
                    if line.startswith("__version__"):
                        return line.split("=")[1].strip().strip('"\'')
        except Exception:
            pass
    
    return "1.0.0"


def collect_all_dependencies() -> List[Dependency]:
    """Collect all dependencies from various sources."""
    deps: List[Dependency] = []
    
    # Scan installed
    print_step("Scanning installed dependencies...")
    installed = get_installed_dependencies()
    deps.extend(installed)
    print_metric(f"Found {len(installed)} installed packages")
    
    # Scan requirements.txt
    req_path = Path("requirements.txt")
    if req_path.exists():
        print_step(f"Scanning {req_path}...")
        req_deps = scan_requirements_file(req_path)
        deps.extend(req_deps)
        print_metric(f"Found {len(req_deps)} requirements")
    
    # Scan requirements-dev.txt
    dev_req_path = Path("requirements-dev.txt")
    if dev_req_path.exists():
        print_step(f"Scanning {dev_req_path}...")
        dev_deps = scan_requirements_file(dev_req_path)
        for dep in dev_deps:
            dep.purpose = "dev"
        deps.extend(dev_deps)
        print_metric(f"Found {len(dev_deps)} dev requirements")
    
    # Deduplicate
    seen = set()
    unique_deps = []
    for dep in deps:
        key = (dep.name.lower(), dep.version)
        if key not in seen:
            seen.add(key)
            unique_deps.append(dep)
    
    return unique_deps


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="H-S-Tool SBOM Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/sbom_generate.py --format cyclonedx --output sbom/cyclonedx.json
  python tools/sbom_generate.py --format spdx --output sbom/spdx.json
  python tools/sbom_generate.py --validate --path sbom/cyclonedx.json
  python tools/sbom_generate.py --update
        """,
    )
    
    parser.add_argument(
        "--format",
        choices=["cyclonedx", "spdx"],
        default="cyclonedx",
        help="SBOM format (default: cyclonedx).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path.",
    )
    parser.add_argument(
        "--project-name",
        type=str,
        default="H-S-Tool",
        help="Project name for SBOM.",
    )
    parser.add_argument(
        "--project-version",
        type=str,
        default=None,
        help="Project version for SBOM.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate existing SBOM file.",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Path to SBOM file for validation.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update all SBOM files.",
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
    
    # Validation mode
    if args.validate:
        if not args.path:
            print_error("Please specify --path for validation")
            return 1
        
        sbom_path = Path(args.path)
        print_step(f"Validating {sbom_path}...")
        
        is_valid, errors = validate_sbom(sbom_path)
        
        if is_valid:
            print_ok("SBOM validation PASSED")
            return 0
        else:
            print_error("SBOM validation FAILED")
            for error in errors:
                print_error(f"  {error}")
            return 1
    
    # Collect dependencies
    print_step("Collecting dependencies...")
    deps = collect_all_dependencies()
    print_metric(f"Total dependencies: {len(deps)}")
    
    # Get project version
    project_version = args.project_version or get_project_version()
    print_detail(f"Project version: {project_version}")
    
    # Generate SBOM
    if args.format == "cyclonedx":
        print_step("Generating CycloneDX SBOM...")
        sbom = generate_cyclonedx_sbom(
            deps=deps,
            project_name=args.project_name,
            project_version=project_version,
        )
    else:
        print_step("Generating SPDX SBOM...")
        sbom = generate_spdx_sbom(
            deps=deps,
            project_name=args.project_name,
            project_version=project_version,
        )
    
    # Output
    if args.output:
        output_path = Path(args.output)
        save_sbom(sbom, output_path, args.format)
    else:
        # Default output paths
        sbom_dir = Path("sbom")
        sbom_dir.mkdir(parents=True, exist_ok=True)
        
        if args.format == "cyclonedx":
            output_path = sbom_dir / "cyclonedx.json"
        else:
            output_path = sbom_dir / "spdx.json"
        
        save_sbom(sbom, output_path, args.format)
    
    # Update mode
    if args.update:
        print_step("Updating all SBOM files...")
        
        # CycloneDX
        cyclonedx_sbom = generate_cyclonedx_sbom(
            deps=deps,
            project_name=args.project_name,
            project_version=project_version,
        )
        save_sbom(cyclonedx_sbom, Path("sbom/cyclonedx.json"), "cyclonedx")
        
        # SPDX
        spdx_sbom = generate_spdx_sbom(
            deps=deps,
            project_name=args.project_name,
            project_version=project_version,
        )
        save_sbom(spdx_sbom, Path("sbom/spdx.json"), "spdx")
        
        print_ok("All SBOM files updated")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
