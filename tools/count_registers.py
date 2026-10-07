from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.db import connect, init_db


def main() -> int:
    company_id = sys.argv[1] if len(sys.argv) > 1 else "LLC_TEST_ALPHA"

    init_db()

    with connect() as conn:
        for table in ("departments", "positions", "employees"):
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE company_id = ?",
                (company_id,),
            ).fetchone()[0]

            print(f"{table}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())