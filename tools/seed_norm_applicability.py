from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.applicability_db import (
    init_applicability_schema,
    upsert_applicability,
)
from ot_agent.db import company_exists, init_db
from ot_agent.regulatory_db import init_regulatory_schema, source_exists


ASSIGNMENTS = [
    {
        "company_id": "LLC_TEST_ALPHA",
        "source_id": "SYN_NORM_001",
        "applicability_status": "CONFIRMED",
        "reason": "Synthetic test assignment for warehouse and height workflow.",
        "confirmed_by": "TEST_USER",
    },
    {
        "company_id": "LLC_TEST_ALPHA",
        "source_id": "SYN_NORM_002",
        "applicability_status": "REQUIRES_VERIFICATION",
        "reason": "Synthetic medical metadata placeholder. Not legally verified.",
        "confirmed_by": None,
    },
    {
        "company_id": "LLC_TEST_ALPHA",
        "source_id": "SYN_NORM_003",
        "applicability_status": "REJECTED",
        "reason": "Synthetic operational placeholder not used for this company in test.",
        "confirmed_by": "TEST_USER",
    },
    {
        "company_id": "LLC_TEST_BETA",
        "source_id": "SYN_NORM_001",
        "applicability_status": "REJECTED",
        "reason": "Synthetic warehouse source not relevant for IT/accounting test company.",
        "confirmed_by": "TEST_USER",
    },
    {
        "company_id": "LLC_TEST_BETA",
        "source_id": "SYN_NORM_002",
        "applicability_status": "CONFIRMED",
        "reason": "Synthetic test assignment for medical metadata workflow.",
        "confirmed_by": "TEST_USER",
    },
    {
        "company_id": "LLC_TEST_BETA",
        "source_id": "SYN_NORM_003",
        "applicability_status": "SUGGESTED",
        "reason": "Synthetic suggestion for future operational control tests.",
        "confirmed_by": None,
    },
]


def validate_assignments() -> list[str]:
    errors: list[str] = []

    for item in ASSIGNMENTS:
        company_id = item.get("company_id")
        source_id = item.get("source_id")

        if not company_id:
            errors.append("Assignment has empty company_id.")
            continue

        if not source_id:
            errors.append(f"{company_id}: assignment has empty source_id.")
            continue

        if not company_exists(str(company_id)):
            errors.append(f"Company does not exist: {company_id}")

        if not source_exists(str(source_id)):
            errors.append(f"Regulatory source does not exist: {source_id}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed synthetic norm applicability assignments."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Perform real database write. Without this flag, dry-run only.",
    )

    args = parser.parse_args()

    init_db()
    init_regulatory_schema()
    init_applicability_schema()

    errors = validate_assignments()

    print("=== SYNTHETIC APPLICABILITY SEED DIAGNOSTICS ===")
    print(f"assignments: {len(ASSIGNMENTS)}")

    if errors:
        print("\nERRORS:")
        for error in errors:
            print(f"- {error}")
        print("\nSeed aborted.")
        return 1

    for item in ASSIGNMENTS:
        print(
            f"{item['company_id']} | "
            f"{item['source_id']} | "
            f"{item['applicability_status']}"
        )

    if not args.commit:
        print("\nDRY-RUN completed successfully. No database write was performed.")
        print("Run with --commit to write data.")
        return 0

    for item in ASSIGNMENTS:
        upsert_applicability(item)

    print("\nSEED COMPLETED SUCCESSFULLY.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())