import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.periodic_control_db import (
    get_connection,
    init_periodic_schema,
    list_employees,
    upsert_event,
)

DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

TARGET_COMPANIES = [
    "LLC_TEST_ALPHA",
    "LLC_TEST_BETA",
]


def iso(value: date) -> str:
    return value.isoformat()


def build_samples(today: date) -> list[tuple]:
    return [
        (
            "MEDICAL_EXAM",
            "SYNTHETIC_EXPIRED",
            iso(today - timedelta(days=400)),
            None,
            365,
            None,
            0,
            "synthetic expired example",
            "No legal periodicity implied",
        ),
        (
            "PSYCHIATRIC_EXAM",
            "SYNTHETIC_DUE_SOON",
            iso(today - timedelta(days=350)),
            None,
            365,
            None,
            0,
            "synthetic due soon example",
            "No legal periodicity implied",
        ),
        (
            "TRAINING",
            "SYNTHETIC_OK",
            iso(today - timedelta(days=100)),
            None,
            365,
            None,
            0,
            "synthetic ok example",
            "No legal periodicity implied",
        ),
        (
            "BRIEFING",
            "SYNTHETIC_OK",
            iso(today - timedelta(days=5)),
            None,
            90,
            None,
            0,
            "synthetic ok example",
            "No legal periodicity implied",
        ),
        (
            "KNOWLEDGE_CHECK",
            "SYNTHETIC_NO_DATA",
            None,
            None,
            None,
            "NO_DATA",
            0,
            "synthetic missing data example",
            "No legal periodicity implied",
        ),
        (
            "OTHER",
            "SYNTHETIC_RESTRICTED",
            iso(today - timedelta(days=10)),
            iso(today + timedelta(days=10)),
            None,
            "R",
            1,
            "synthetic restricted metadata example",
            "No diagnosis stored",
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed synthetic periodic control events."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write changes. Without this flag the run is dry-run.",
    )
    args = parser.parse_args()

    init_periodic_schema(DB_PATH)

    conn = get_connection(DB_PATH)
    planned = 0

    try:
        today = date.today()
        samples = build_samples(today)

        for company_id in TARGET_COMPANIES:
            employees = list_employees(conn, company_id)

            if not employees:
                print(f"SKIP {company_id}: no employees")
                continue

            for employee in employees:
                for sample in samples:
                    upsert_event(
                        conn,
                        company_id=company_id,
                        employee_id=employee["employee_id"],
                        event_type=sample[0],
                        event_code=sample[1],
                        performed_at=sample[2],
                        valid_until=sample[3],
                        interval_days=sample[4],
                        result_code=sample[5],
                        restriction_flag=sample[6],
                        reference_note=sample[7],
                        note=sample[8],
                    )
                    planned += 1

        if args.commit:
            conn.commit()
            print(f"COMMIT: YES | planned_events: {planned}")
        else:
            conn.rollback()
            print(f"COMMIT: NO (dry-run) | planned_events: {planned}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
