import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.electrical_safety_db import (
    get_connection,
    summary,
    validate_integrity,
)


def main() -> int:
    conn = get_connection()

    try:
        snap = summary(conn)
        errors = validate_integrity(conn)

        print("SUMMARY=" + json.dumps(snap, ensure_ascii=True, sort_keys=True))

        if errors:
            print("ELECTRICAL_CHECK_FAILED")
            for error in errors[:50]:
                print("ERROR=" + error)
            return 1

        print("ELECTRICAL_CHECK_OK")
        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
