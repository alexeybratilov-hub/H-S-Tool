from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.db import connect, init_db

TABLES = (
    "departments",
    "positions",
    "employees",
)


def main() -> int:
    init_db()

    violations: list[str] = []

    with connect() as conn:
        companies = [
            row["company_id"]
            for row in conn.execute(
                "SELECT company_id FROM companies ORDER BY company_id"
            )
        ]

        if not companies:
            print("Companies: none")
            return 0

        print("Companies:", ", ".join(companies))
        print()

        for company_id in companies:
            print(f"Company {company_id}:")

            for table in TABLES:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE company_id = ?",
                    (company_id,),
                ).fetchone()[0]

                print(f"  {table}: {count}")

            print()

        rows = conn.execute(
            """
            SELECT
                e.employee_id,
                e.company_id AS employee_company,
                p.company_id AS position_company,
                d.company_id AS department_company
            FROM employees e
            LEFT JOIN positions p
                ON p.position_id = e.position_id
            LEFT JOIN departments d
                ON d.department_id = e.department_id
            WHERE (
                    e.position_id IS NOT NULL
                    AND (
                        p.position_id IS NULL
                        OR p.company_id != e.company_id
                    )
                )
                OR (
                    e.department_id IS NOT NULL
                    AND (
                        d.department_id IS NULL
                        OR d.company_id != e.company_id
                    )
                )
            """
        ).fetchall()

        for row in rows:
            violations.append(
                f"employee {row['employee_id']} company {row['employee_company']} "
                f"has invalid position company {row['position_company']} "
                f"or department company {row['department_company']}"
            )

        rows = conn.execute(
            """
            SELECT
                d.department_id,
                d.company_id AS department_company,
                p.company_id AS parent_company,
                e.company_id AS responsible_company
            FROM departments d
            LEFT JOIN departments p
                ON p.department_id = d.parent_department_id
            LEFT JOIN employees e
                ON e.employee_id = d.responsible_employee_id
            WHERE (
                    d.parent_department_id IS NOT NULL
                    AND (
                        p.department_id IS NULL
                        OR p.company_id != d.company_id
                    )
                )
                OR (
                    d.responsible_employee_id IS NOT NULL
                    AND (
                        e.employee_id IS NULL
                        OR e.company_id != d.company_id
                    )
                )
            """
        ).fetchall()

        for row in rows:
            violations.append(
                f"department {row['department_id']} company {row['department_company']} "
                f"has invalid parent company {row['parent_company']} "
                f"or responsible employee company {row['responsible_company']}"
            )

        rows = conn.execute(
            """
            SELECT
                pos.position_id,
                pos.company_id AS position_company,
                d.company_id AS department_company
            FROM positions pos
            LEFT JOIN departments d
                ON d.department_id = pos.department_id
            WHERE pos.department_id IS NOT NULL
              AND (
                    d.department_id IS NULL
                    OR d.company_id != pos.company_id
                )
            """
        ).fetchall()

        for row in rows:
            violations.append(
                f"position {row['position_id']} company {row['position_company']} "
                f"has invalid department company {row['department_company']}"
            )

    if violations:
        print("ISOLATION VIOLATIONS:")

        for violation in violations:
            print(f"- {violation}")

        return 1

    print("OK: company isolation checks passed at database level.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())