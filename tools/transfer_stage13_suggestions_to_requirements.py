import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.stage13_requirement_transfer_db import (
    get_connection,
    insert_rows,
    plan_transfer,
    validate_transfer,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transfer preliminary Stage 13 suggestions to document_requirements."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write changes. Without this flag the run is dry-run.",
    )
    args = parser.parse_args()

    conn = get_connection()

    try:
        rows, issues = plan_transfer(conn)

        print(f"DRY_RUN={'NO' if args.commit else 'YES'} | planned={len(rows)} | issues={len(issues)}")

        if issues:
            for issue in issues[:30]:
                print("ISSUE=" + issue)

            print("DRY_RUN_ISSUES")
            return 2

        if len(rows) <= 0:
            print("DRY_RUN_EMPTY")
            return 2

        print("DRY_RUN_OK")

        if not args.commit:
            return 0

        inserted = insert_rows(conn, rows)
        validation_errors = validate_transfer(conn)

        if validation_errors:
            conn.rollback()

            for error in validation_errors:
                print("VALIDATION_ERROR=" + error)

            print("TRANSFER_VALIDATION_FAILED")
            return 3

        conn.commit()
        print(f"COMMIT: YES | inserted={inserted}")
        print("TRANSFER_OK")
        return 0

    except Exception as exc:
        conn.rollback()
        print(f"TRANSFER_ERROR={exc}")
        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
