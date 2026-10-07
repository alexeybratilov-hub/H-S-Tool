from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.db import connect, init_db

ALPHA_DIR = BASE_DIR / "06_TESTS" / "synthetic_registers" / "LLC_TEST_ALPHA"
BETA_DIR = BASE_DIR / "06_TESTS" / "synthetic_registers" / "LLC_TEST_BETA"

STAFFING_HEADER = [
    "schedule_id",
    "company_id",
    "row_id",
    "department_id",
    "position_id",
    "headcount",
    "effective_date",
    "approved_date",
]

ALPHA_STAFFING_ROWS = [
    [
        "SCH_2026_01_01_ALPHA",
        "LLC_TEST_ALPHA",
        "SR_ALPHA_001",
        "DEP_MAIN",
        "POS_DIRECTOR",
        1,
        "2026-01-01",
        "2025-12-30",
    ],
    [
        "SCH_2026_01_01_ALPHA",
        "LLC_TEST_ALPHA",
        "SR_ALPHA_002",
        "DEP_OT",
        "POS_OT_SPECIALIST",
        1,
        "2026-01-01",
        "2025-12-30",
    ],
    [
        "SCH_2026_01_01_ALPHA",
        "LLC_TEST_ALPHA",
        "SR_ALPHA_003",
        "DEP_WAREHOUSE",
        "POS_WAREHOUSE_MANAGER",
        1,
        "2026-01-01",
        "2025-12-30",
    ],
    [
        "SCH_2026_01_01_ALPHA",
        "LLC_TEST_ALPHA",
        "SR_ALPHA_004",
        "DEP_WAREHOUSE",
        "POS_STOREKEEPER",
        2,
        "2026-01-01",
        "2025-12-30",
    ],
]

BETA_STAFFING_ROWS = [
    [
        "SCH_2026_01_01_BETA",
        "LLC_TEST_BETA",
        "SR_BETA_001",
        "DEP_MAIN_B",
        "POS_DIRECTOR_B",
        1,
        "2026-01-01",
        "2025-12-30",
    ],
    [
        "SCH_2026_01_01_BETA",
        "LLC_TEST_BETA",
        "SR_BETA_002",
        "DEP_IT",
        "POS_IT_LEAD_B",
        1,
        "2026-01-01",
        "2025-12-30",
    ],
    [
        "SCH_2026_01_01_BETA",
        "LLC_TEST_BETA",
        "SR_BETA_003",
        "DEP_ACCOUNTING",
        "POS_ACCOUNTANT_B",
        1,
        "2026-01-01",
        "2025-12-30",
    ],
]

SYNTHETIC_JOB_TEXT = (
    "Synthetic job description for testing data pipeline. "
    "Not a legal document. "
    "No personal data. "
    "Requires verification by an occupational health and safety specialist before any use."
)


def get_position_title(conn, position_id: str) -> str:
    row = conn.execute(
        "SELECT title FROM positions WHERE position_id = ?",
        (position_id,),
    ).fetchone()

    if not row:
        raise ValueError(f"Position not found: {position_id}")

    return str(row["title"])


def write_staffing_csv(path: Path, rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(STAFFING_HEADER)
        writer.writerows(rows)

    print(f"Created: {path.relative_to(BASE_DIR).as_posix()}")


def build_job_descriptions(company_id: str, position_ids: list[str]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    with connect() as conn:
        for index, position_id in enumerate(position_ids, start=1):
            title = get_position_title(conn, position_id)

            items.append(
                {
                    "job_description_id": f"JD_{company_id}_{index:03d}",
                    "company_id": company_id,
                    "position_id": position_id,
                    "title": title,
                    "source_file": "synthetic_job_description.txt",
                    "text_content": SYNTHETIC_JOB_TEXT,
                    "version": "v01",
                    "status": "RAW",
                    "effective_date": "2026-01-01",
                }
            )

    return items


def write_job_descriptions_json(path: Path, items: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(items, file, ensure_ascii=False, indent=2)

    print(f"Created: {path.relative_to(BASE_DIR).as_posix()}")


def main() -> int:
    init_db()

    write_staffing_csv(ALPHA_DIR / "staffing_schedule.csv", ALPHA_STAFFING_ROWS)
    write_staffing_csv(BETA_DIR / "staffing_schedule.csv", BETA_STAFFING_ROWS)

    alpha_jobs = build_job_descriptions(
        "LLC_TEST_ALPHA",
        [
            "POS_OT_SPECIALIST",
            "POS_WAREHOUSE_MANAGER",
        ],
    )

    beta_jobs = build_job_descriptions(
        "LLC_TEST_BETA",
        [
            "POS_IT_LEAD_B",
        ],
    )

    write_job_descriptions_json(ALPHA_DIR / "job_descriptions.json", alpha_jobs)
    write_job_descriptions_json(BETA_DIR / "job_descriptions.json", beta_jobs)

    print("Synthetic staffing and job description files created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())