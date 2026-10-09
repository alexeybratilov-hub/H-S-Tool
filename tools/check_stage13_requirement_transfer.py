import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

SOURCE_TYPE = "STAGE13_PRELIMINARY"
TARGET_STATUS = "REQUIRES_VERIFICATION"

errors = []


def q(cur, sql, params=()):
    return cur.execute(sql, params).fetchall()


def main() -> int:
    if not DB_PATH.exists():
        print("STAGE13_TRANSFER_CHECK_FAILED")
        print("ERROR=database missing")
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    table_exists = (
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='document_requirements'"
        ).fetchone()
        is not None
    )

    if not table_exists:
        errors.append("document_requirements table missing")
    else:
        cols = {row[1] for row in cur.execute("PRAGMA table_info(document_requirements)").fetchall()}

        if "source_type" not in cols:
            errors.append("document_requirements.source_type missing")
        else:
            rows = q(
                cur,
                "SELECT COUNT(*) AS c FROM document_requirements WHERE source_type = ?",
                (SOURCE_TYPE,),
            )[0]["c"]

            print(f"transferred_requirements_rows={rows}")

            if rows <= 0:
                errors.append("no transferred requirements found")

            if "status" in cols:
                bad_status = q(
                    cur,
                    """
                    SELECT COUNT(*) AS c
                    FROM document_requirements
                    WHERE source_type = ?
                      AND status <> ?
                    """,
                    (SOURCE_TYPE, TARGET_STATUS),
                )[0]["c"]

                print(f"bad_status_rows={bad_status}")

                if bad_status:
                    errors.append("transferred requirements with unexpected status")

            if "company_id" in cols:
                orphan = q(
                    cur,
                    f"""
                    SELECT COUNT(*) AS c
                    FROM document_requirements
                    WHERE source_type = ?
                      AND (
                        company_id IS NULL
                        OR company_id NOT IN (SELECT company_id FROM companies)
                      )
                    """,
                    (SOURCE_TYPE,),
                )[0]["c"]

                print(f"orphan_company_rows={orphan}")

                if orphan:
                    errors.append("transferred requirements with orphan company_id")

            if "requirement_id" in cols:
                dup = q(
                    cur,
                    f"""
                    SELECT COUNT(*) AS c
                    FROM (
                      SELECT requirement_id
                      FROM document_requirements
                      WHERE source_type = ?
                      GROUP BY requirement_id
                      HAVING COUNT(*) > 1
                    )
                    """,
                    (SOURCE_TYPE,),
                )[0]["c"]

                print(f"duplicate_requirement_ids={dup}")

                if dup:
                    errors.append("duplicate transferred requirement_id rows")

            if "source_id" in cols:
                dup_source = q(
                    cur,
                    f"""
                    SELECT COUNT(*) AS c
                    FROM (
                      SELECT company_id, source_id
                      FROM document_requirements
                      WHERE source_type = ?
                      GROUP BY company_id, source_id
                      HAVING COUNT(*) > 1
                    )
                    """,
                    (SOURCE_TYPE,),
                )[0]["c"]

                print(f"duplicate_source_ids={dup_source}")

                if dup_source:
                    errors.append("duplicate transferred source_id rows")

    conn.close()

    if errors:
        print("STAGE13_TRANSFER_CHECK_FAILED")
        for error in errors:
            print("ERROR=" + error)
        return 1

    print("STAGE13_TRANSFER_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
