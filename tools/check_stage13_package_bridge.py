import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

errors = []


def q(cur, sql, params=()):
    return cur.execute(sql, params).fetchall()


def main() -> int:
    if not DB_PATH.exists():
        print("BRIDGE_CHECK_FAILED")
        print("ERROR=database missing")
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    table_exists = (
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stage13_package_suggestions'"
        ).fetchone()
        is not None
    )

    if not table_exists:
        errors.append("stage13_package_suggestions table missing")
    else:
        rows = q(cur, "SELECT COUNT(*) AS c FROM stage13_package_suggestions")[0]["c"]
        print(f"stage13_package_suggestions_rows={rows}")

        if rows <= 0:
            errors.append("stage13_package_suggestions is empty")

        orphan = q(
            cur,
            """
            SELECT COUNT(*) AS c
            FROM stage13_package_suggestions
            WHERE company_id IS NULL
               OR company_id NOT IN (SELECT company_id FROM companies)
            """,
        )[0]["c"]

        print(f"stage13_package_suggestions_orphan_company_rows={orphan}")

        if orphan:
            errors.append("orphan company rows found")

        bad_status = q(
            cur,
            """
            SELECT COUNT(*) AS c
            FROM stage13_package_suggestions
            WHERE status <> 'PRELIMINARY'
               OR verification_status <> 'REQUIRES_VERIFICATION'
            """,
        )[0]["c"]

        print(f"stage13_package_suggestions_bad_status_rows={bad_status}")

        if bad_status:
            errors.append("non-preliminary status rows found")

        bad_kind = q(
            cur,
            """
            SELECT COUNT(*) AS c
            FROM stage13_package_suggestions
            WHERE source_kind NOT IN ('SOUT', 'RISK', 'PPE')
            """,
        )[0]["c"]

        print(f"stage13_package_suggestions_bad_source_kind_rows={bad_kind}")

        if bad_kind:
            errors.append("unexpected source_kind rows found")

        by_kind = q(
            cur,
            """
            SELECT source_kind, COUNT(*) AS c
            FROM stage13_package_suggestions
            GROUP BY source_kind
            ORDER BY source_kind
            """,
        )

        print("stage13_package_suggestions_by_kind=")

        for row in by_kind:
            print(f"{row['source_kind']}={row['c']}")

        dupes = q(
            cur,
            """
            SELECT suggestion_id, COUNT(*) AS c
            FROM stage13_package_suggestions
            GROUP BY suggestion_id
            HAVING COUNT(*) > 1
            """,
        )

        print(f"stage13_package_suggestions_duplicate_ids={len(dupes)}")

        if dupes:
            errors.append("duplicate suggestion_id rows found")

    conn.close()

    if errors:
        print("BRIDGE_CHECK_FAILED")
        for error in errors:
            print("ERROR=" + error)
        return 1

    print("BRIDGE_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
