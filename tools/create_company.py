from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.db import company_exists, create_company, init_db


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a company in the local SQLite database."
    )
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--legal-name", required=True)

    args = parser.parse_args()

    company_id = str(args.company_id).strip()
    legal_name = str(args.legal_name).strip()

    if not company_id:
        print("ERROR: company_id is required.")
        return 1

    if not legal_name:
        print("ERROR: legal_name is required.")
        return 1

    init_db()

    if company_exists(company_id):
        print(f"Company already exists: {company_id}")
        return 0

    created = create_company(
        {
            "company_id": company_id,
            "legal_name": legal_name,
        }
    )

    print(f"Created company: {created['company_id']} | {created['legal_name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())