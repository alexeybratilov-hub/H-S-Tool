import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.electrical_safety_db import (
    get_connection,
    seed_synthetic,
    summary,
    validate_integrity,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed synthetic Stage 14 electrical safety technical data."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write changes. Without this flag the run is dry-run and rolled back.",
    )
    args = parser.parse_args()

    conn = get_connection()
    conn.isolation_level = None

    try:
        conn.execute("BEGIN IMMEDIATE")

        stats = seed_synthetic(conn)
        errors = validate_integrity(conn)
        snap = summary(conn)

        print("DRY_RUN=" + ("NO" if args.commit else "YES"))
        print("SEED_STATS=" + json.dumps(stats, ensure_ascii=True, sort_keys=True))
        print("SUMMARY=" + json.dumps(snap, ensure_ascii=True, sort_keys=True))

        if errors:
            for error in errors[:50]:
                print("SEED_VALIDATION_ERROR=" + error)

            conn.execute("ROLLBACK")
            print("SEED_VALIDATION_FAILED")
            return 3

        if args.commit:
            conn.execute("COMMIT")
            print("SEED_COMMITTED")
        else:
            conn.execute("ROLLBACK")
            print("SEED_ROLLED_BACK")

        print("SEED_OK")
        return 0

    except Exception as exc:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass

        print("SEED_ERROR=" + str(exc))
        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
