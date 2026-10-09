import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.ppe_sout_risk_db import DB_PATH, get_connection, init_schema

HARMFUL_FACTORS = [
    ("HF_NOISE", "HF_NOISE", "Synthetic noise factor", "Technical synthetic factor only."),
    ("HF_DUST", "HF_DUST", "Synthetic dust factor", "Technical synthetic factor only."),
    ("HF_ELECTRICAL", "HF_ELECTRICAL", "Synthetic electrical factor", "Technical synthetic factor only."),
    ("HF_FALL", "HF_FALL", "Synthetic fall factor", "Technical synthetic factor only."),
    ("HF_FIRE", "HF_FIRE", "Synthetic fire factor", "Technical synthetic factor only."),
    ("HF_LIFT", "HF_LIFT", "Synthetic manual lifting factor", "Technical synthetic factor only."),
]

PPE_ITEMS = [
    ("PPE_HELMET", "PPE_HELMET", "Synthetic helmet", "Technical synthetic PPE item only."),
    ("PPE_GLOVES", "PPE_GLOVES", "Synthetic gloves", "Technical synthetic PPE item only."),
    ("PPE_RESPIRATOR", "PPE_RESPIRATOR", "Synthetic respirator", "Technical synthetic PPE item only."),
    ("PPE_EYE", "PPE_EYE", "Synthetic eye protection", "Technical synthetic PPE item only."),
    ("PPE_FOOT", "PPE_FOOT", "Synthetic footwear", "Technical synthetic PPE item only."),
    ("PPE_VEST", "PPE_VEST", "Synthetic high visibility vest", "Technical synthetic PPE item only."),
]

HARMFUL_FACTOR_IDS = [x[0] for x in HARMFUL_FACTORS]
PPE_ITEM_IDS = [x[0] for x in PPE_ITEMS]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed synthetic Stage 13 SOUT/PPE/risk data."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually write changes. Without this flag the run is dry-run.",
    )
    args = parser.parse_args()

    init_schema(DB_PATH)
    conn = get_connection(DB_PATH)
    planned = 0

    try:
        for factor_id, code, title, description in HARMFUL_FACTORS:
            conn.execute(
                """
                INSERT OR REPLACE INTO harmful_factors
                (factor_id, code, title, topic, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (factor_id, code, title, "OT", description),
            )
            planned += 1

        for item_id, code, title, description in PPE_ITEMS:
            conn.execute(
                """
                INSERT OR REPLACE INTO ppe_items
                (item_id, code, title, topic, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item_id, code, title, "OT", description),
            )
            planned += 1

        companies = [
            row[0]
            for row in conn.execute(
                "SELECT company_id FROM companies ORDER BY company_id"
            ).fetchall()
        ]

        for company_id in companies:
            campaign_id = f"SC:{company_id}:SYNTH"

            conn.execute(
                """
                INSERT OR REPLACE INTO sout_campaigns
                (campaign_id, company_id, title, status, organization_name,
                 contract_number, date_start, date_end, source_note,
                 verification_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign_id,
                    company_id,
                    "Synthetic SOUT campaign",
                    "REQUIRES_VERIFICATION",
                    "SYNTH_ORG",
                    "SYNTH_CONTRACT",
                    "2026-01-01",
                    "2026-01-31",
                    "synthetic only",
                    "REQUIRES_VERIFICATION",
                ),
            )
            planned += 1

            positions = conn.execute(
                """
                SELECT position_id, department_id
                FROM positions
                WHERE company_id = ?
                ORDER BY position_id
                """,
                (company_id,),
            ).fetchall()

            for pos in positions:
                position_id = pos["position_id"]
                department_id = pos["department_id"]
                workplace_id = f"SW:{company_id}:{position_id}"

                conn.execute(
                    """
                    INSERT OR REPLACE INTO sout_workplaces
                    (workplace_id, company_id, department_id, position_id,
                     employee_id, workplace_code, title, status, source_note,
                     verification_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workplace_id,
                        company_id,
                        department_id,
                        position_id,
                        None,
                        f"WP-{position_id}",
                        "Synthetic workplace",
                        "REQUIRES_VERIFICATION",
                        "synthetic only",
                        "REQUIRES_VERIFICATION",
                    ),
                )
                planned += 1

                for factor_id in HARMFUL_FACTOR_IDS[:2]:
                    result_id = f"SR:{workplace_id}:{factor_id}"
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO sout_results
                        (result_id, campaign_id, workplace_id, factor_id,
                         class_code, class_title, measurement_value,
                         measurement_unit, source_chunk_id, verification_status,
                         note)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            result_id,
                            campaign_id,
                            workplace_id,
                            factor_id,
                            "SYN_CLASS_3",
                            "Synthetic hazard class",
                            1.0,
                            "synthetic_unit",
                            None,
                            "REQUIRES_VERIFICATION",
                            "synthetic only",
                        ),
                    )
                    planned += 1

                for item_id in PPE_ITEM_IDS[:2]:
                    norm_id = f"PN:{company_id}:{position_id}:{item_id}"
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO ppe_norms
                        (norm_id, company_id, position_id, factor_id, item_id,
                         quantity, unit, validity_days, status, source_note,
                         verification_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            norm_id,
                            company_id,
                            position_id,
                            HARMFUL_FACTOR_IDS[0],
                            item_id,
                            1,
                            "pcs",
                            365,
                            "REQUIRES_VERIFICATION",
                            "synthetic only",
                            "REQUIRES_VERIFICATION",
                        ),
                    )
                    planned += 1

                risk_id = f"RR:{company_id}:{position_id}:{HARMFUL_FACTOR_IDS[0]}"
                conn.execute(
                    """
                    INSERT OR REPLACE INTO risk_register
                    (risk_id, company_id, position_id, workplace_id, factor_id,
                     description, likelihood_code, severity_code,
                     risk_level_code, control_measures, status, source_note,
                     verification_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        risk_id,
                        company_id,
                        position_id,
                        workplace_id,
                        HARMFUL_FACTOR_IDS[0],
                        "Synthetic risk",
                        "SYN_L3",
                        "SYN_S3",
                        "SYN_MEDIUM",
                        "synthetic controls",
                        "REQUIRES_VERIFICATION",
                        "synthetic only",
                        "REQUIRES_VERIFICATION",
                    ),
                )
                planned += 1

            employees = conn.execute(
                """
                SELECT employee_id
                FROM employees
                WHERE company_id = ?
                ORDER BY employee_id
                """,
                (company_id,),
            ).fetchall()

            for emp in employees:
                employee_id = emp["employee_id"]
                card_id = f"PC:{company_id}:{employee_id}"

                conn.execute(
                    """
                    INSERT OR REPLACE INTO employee_ppe_cards
                    (card_id, company_id, employee_id, status, note,
                     verification_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        card_id,
                        company_id,
                        employee_id,
                        "REQUIRES_VERIFICATION",
                        "synthetic only",
                        "REQUIRES_VERIFICATION",
                    ),
                )
                planned += 1

                item_id = PPE_ITEM_IDS[0]
                issue_id = f"PI:{company_id}:{employee_id}:{item_id}"

                conn.execute(
                    """
                    INSERT OR REPLACE INTO ppe_issue_records
                    (record_id, card_id, company_id, employee_id, item_id,
                     quantity, issued_at, return_due_at, status, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        issue_id,
                        card_id,
                        company_id,
                        employee_id,
                        item_id,
                        1,
                        "2026-10-01",
                        "2027-10-01",
                        "REQUIRES_VERIFICATION",
                        "synthetic only",
                    ),
                )
                planned += 1

                return_id = f"PR:{issue_id}"

                conn.execute(
                    """
                    INSERT OR REPLACE INTO ppe_return_records
                    (return_id, issue_record_id, company_id, employee_id,
                     item_id, returned_at, condition_code, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        return_id,
                        issue_id,
                        company_id,
                        employee_id,
                        item_id,
                        "2027-09-30",
                        "SYN_OK",
                        "synthetic only",
                    ),
                )
                planned += 1

        if args.commit:
            conn.commit()
            print(f"COMMIT: YES | planned_rows: {planned}")
        else:
            conn.rollback()
            print(f"COMMIT: NO (dry-run) | planned_rows: {planned}")

        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
