import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.position_profiles_db import (
    ensure_profile,
    get_connection,
    init_position_profiles_schema,
    list_positions_for_company,
    upsert_link,
)

DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

TARGET_COMPANIES = [
    "LLC_TEST_ALPHA",
    "LLC_TEST_BETA",
]

LINK_PLAN = [
    ("duty", "DUTY_OT_GENERAL"),
    ("hazard", "HAZ_OT_PHYSICAL"),
    ("work", "WT_OT_OFFICE"),
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed synthetic position profile links."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write changes. Without this flag the run is dry-run.",
    )
    args = parser.parse_args()

    init_position_profiles_schema(DB_PATH)

    conn = get_connection(DB_PATH)
    planned = 0

    try:
        for company_id in TARGET_COMPANIES:
            positions = list_positions_for_company(conn, company_id)

            if not positions:
                print(f"SKIP {company_id}: no positions")
                continue

            for position in positions:
                position_id = position["position_id"]

                ensure_profile(conn, company_id, position_id)

                for link_type, code in LINK_PLAN:
                    upsert_link(
                        conn,
                        company_id,
                        position_id,
                        link_type,
                        code,
                        "SUGGESTED",
                        "synthetic_seed",
                        "[REQUIRES_VERIFICATION]",
                    )
                    planned += 1

        if args.commit:
            conn.commit()
            print(f"COMMIT: YES | planned_links: {planned}")
        else:
            conn.rollback()
            print(f"COMMIT: NO (dry-run) | planned_links: {planned}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
