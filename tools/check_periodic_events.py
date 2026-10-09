import argparse
import sqlite3
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.periodic_control_db import compute_event_status


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only diagnostic for periodic_events table."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Reserved for future machine-readable output. Currently ignored.",
    )
    args = parser.parse_args()

    print("db_path=", DB_PATH)
    print("db_exists=", DB_PATH.exists())

    if not DB_PATH.exists():
        print("ERROR= database missing")
        return 2

    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='periodic_events'"
    )
    table_exists = cur.fetchone() is not None

    print("periodic_events_exists=", table_exists)

    if not table_exists:
        con.close()
        print("ERROR= periodic_events table missing")
        return 1

    cur.execute(
        """
        SELECT *
        FROM periodic_events
        ORDER BY company_id, employee_id, event_type, event_code
        """
    )
    rows = [dict(row) for row in cur.fetchall()]
    con.close()

    today = date.today()

    status_counter = Counter()
    by_company = {}
    by_event_type = {}
    samples = []

    for event in rows:
        computed = compute_event_status(event, today)

        if isinstance(computed, dict):
            status = computed.get("status")
        else:
            status = computed

        status_counter[status] += 1

        company_id = event.get("company_id")
        event_type = event.get("event_type")

        by_company.setdefault(company_id, Counter())[status] += 1
        by_event_type.setdefault(event_type, Counter())[status] += 1

        if len(samples) < 12:
            samples.append(
                (
                    company_id,
                    event.get("employee_id"),
                    event_type,
                    event.get("event_code"),
                    status,
                )
            )

    print("today=", today.isoformat())
    print("rows=", len(rows))
    print("status_counts=", dict(status_counter))
    print("by_company_status_counts=", {k: dict(v) for k, v in by_company.items()})
    print("by_event_type_status_counts=", {k: dict(v) for k, v in by_event_type.items()})
    print("sample_computed_statuses=")

    for sample in samples:
        print(sample)

    print("note= synthetic technical control only; legal periodicities require verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
