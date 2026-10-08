import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.package_planner_db import (
    generate_requirements_for_company,
    get_connection,
    init_package_schema,
    list_companies,
)

DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic document requirements from baseline catalog."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write changes. Without this flag the run is dry-run.",
    )
    args = parser.parse_args()

    init_package_schema(DB_PATH)

    conn = get_connection(DB_PATH)
    total = 0

    try:
        companies = list_companies(conn)

        for company in companies:
            company_id = company["company_id"]
            count = generate_requirements_for_company(conn, company_id)
            total += count
            print(f"COMPANY {company_id}: {count}")

        if args.commit:
            conn.commit()
            print(f"COMMIT: YES | generated_requirements: {total}")
        else:
            conn.rollback()
            print(f"COMMIT: NO (dry-run) | generated_requirements: {total}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
