import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.stage13_confirmed_package_db import (
    get_connection,
    summary,
    validate_sync,
)


def main() -> int:
    conn = get_connection()

    try:
        stats = summary(conn)
        errors = validate_sync(conn)

        print(f"confirmed_requirements={stats['confirmed_requirements']}")
        print(f"technical_packages={stats['technical_packages']}")
        print(f"technical_package_items={stats['technical_package_items']}")

        if errors:
            print("STAGE13_CONFIRMED_PACKAGE_CHECK_FAILED")
            for error in errors[:50]:
                print("ERROR=" + error)
            return 1

        print("STAGE13_CONFIRMED_PACKAGE_CHECK_OK")
        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
