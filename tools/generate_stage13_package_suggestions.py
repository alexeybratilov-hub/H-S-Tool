import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.stage13_package_bridge_db import (
    collect_suggestions,
    get_connection,
    init_bridge_schema,
    insert_suggestions,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate preliminary Stage 13 package suggestions."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write suggestions. Without this flag the run is dry-run.",
    )
    args = parser.parse_args()

    conn = get_connection()

    try:
        suggestions = collect_suggestions(conn)
        planned = len(suggestions)

        if not args.commit:
            print(f"DRY_RUN=YES | planned={planned}")
            print("DRY_RUN_OK")
            return 0

        init_bridge_schema(conn)
        inserted = insert_suggestions(conn, suggestions)
        conn.commit()

        print(f"DRY_RUN=NO | planned={planned} | inserted={inserted}")
        print("COMMIT_OK")
        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
