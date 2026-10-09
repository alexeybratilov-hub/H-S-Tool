import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.stage13_confirmed_package_db import (
    apply_sync,
    get_connection,
    plan_sync,
    summary,
    validate_sync,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize technically confirmed Stage 13 requirements into dedicated draft packages."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write changes. Without this flag the run is dry-run.",
    )
    args = parser.parse_args()

    conn = get_connection()

    try:
        (
            packages_to_create,
            packages_to_remove,
            items_to_add,
            items_to_remove,
            confirmed_ids,
            issues,
        ) = plan_sync(conn)

        print(
            "DRY_RUN="
            + ("NO" if args.commit else "YES")
            + f" | confirmed={len(confirmed_ids)}"
            + f" | packages_create={len(packages_to_create)}"
            + f" | packages_remove={len(packages_to_remove)}"
            + f" | items_add={len(items_to_add)}"
            + f" | items_remove={len(items_to_remove)}"
        )

        if issues:
            for issue in issues[:30]:
                print("ISSUE=" + issue)

            print("SYNC_PLAN_FAILED")
            return 2

        if not args.commit:
            print("DRY_RUN_OK")
            return 0

        stats = apply_sync(
            conn,
            packages_to_create,
            packages_to_remove,
            items_to_add,
            items_to_remove,
        )

        validation_errors = validate_sync(conn)

        if validation_errors:
            conn.rollback()

            for error in validation_errors[:50]:
                print("VALIDATION_ERROR=" + error)

            print("SYNC_VALIDATION_FAILED")
            return 3

        conn.commit()

        print(
            "COMMIT: YES"
            + f" | packages_created={stats['packages_created']}"
            + f" | packages_removed={stats['packages_removed']}"
            + f" | items_added={stats['items_added']}"
            + f" | items_removed={stats['items_removed']}"
        )

        print("SYNC_OK")
        return 0

    except Exception as exc:
        conn.rollback()
        print(f"SYNC_ERROR={exc}")
        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
