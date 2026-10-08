import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.responsibility_db import (
    get_connection,
    init_responsibility_schema,
    list_employees,
    list_roles,
    upsert_assignment,
)

DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

TARGET_COMPANIES = [
    "LLC_TEST_ALPHA",
    "LLC_TEST_BETA",
]

TARGET_ROLE_CODES = [
    "HEAD_ORGANIZATION",
    "OT_RESPONSIBLE",
    "TRAINING_RESPONSIBLE",
]

NOTE = (
    "[\u0423\u0422\u041e\u0427\u041d\u0418\u0422\u042c: "
    "synthetic proposal]"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed synthetic responsibility assignments."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write changes. Without this flag the run is dry-run.",
    )
    args = parser.parse_args()

    init_responsibility_schema(DB_PATH)

    conn = get_connection(DB_PATH)

    try:
        roles = {role["code"]: role["role_id"] for role in list_roles(conn)}
        planned = 0

        for company_id in TARGET_COMPANIES:
            employees = list_employees(conn, company_id)

            if not employees:
                print(f"SKIP {company_id}: no employees")
                continue

            employee = employees[0]

            for role_code in TARGET_ROLE_CODES:
                role_id = roles.get(role_code)

                if not role_id:
                    print(f"SKIP role {role_code}: not found")
                    continue

                upsert_assignment(
                    conn,
                    company_id=company_id,
                    role_id=role_id,
                    employee_id=employee["employee_id"],
                    status="PROPOSED",
                    evidence_note=NOTE,
                    confirmed_by=None,
                    comment="synthetic seed",
                )

                planned += 1

        if args.commit:
            conn.commit()
            print(f"COMMIT: YES | planned_assignments: {planned}")
        else:
            conn.rollback()
            print(f"COMMIT: NO (dry-run) | planned_assignments: {planned}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
