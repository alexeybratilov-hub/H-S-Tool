from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.db import connect, init_db

FILES_TO_CHECK = [
    "src/ot_agent/ui/registers.py",
    "src/ot_agent/ui/companies.py",
    "src/ot_agent/ui/dashboard.py",
    "src/ot_agent/ui/settings.py",
    "app.py",
    "06_TESTS/synthetic_registers/LLC_TEST_ALPHA/departments.csv",
    "06_TESTS/synthetic_registers/LLC_TEST_ALPHA/positions.csv",
    "06_TESTS/synthetic_registers/LLC_TEST_ALPHA/employees.csv",
    "06_TESTS/synthetic_registers/LLC_TEST_BETA/departments.csv",
    "06_TESTS/synthetic_registers/LLC_TEST_BETA/positions.csv",
    "06_TESTS/synthetic_registers/LLC_TEST_BETA/employees.csv",
]


def print_file_head(path: Path) -> None:
    print("\nFILE:", path.relative_to(BASE_DIR).as_posix())

    if not path.exists():
        print("STATUS: MISSING")
        return

    raw = path.read_bytes()
    print("SIZE:", len(raw))
    print("FIRST_BYTES_ASCII:", ascii(raw[:240]))

    try:
        text = raw.decode("utf-8")
        print("UTF8_DECODE: OK")
    except UnicodeDecodeError as exc:
        print("UTF8_DECODE_ERROR:", exc)
        return

    interesting_keywords = [
        "st.tabs",
        "st.subheader",
        "st.title",
        "st.write",
        "department_id",
        "position_id",
        "employee_id",
        "full_name",
        "name",
        "title",
    ]

    printed = 0

    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(keyword in line for keyword in interesting_keywords):
            print(f"LINE_{line_no}_ASCII:", ascii(line))
            printed += 1

            if printed >= 30:
                print("... truncated")
                break


def print_database_values() -> None:
    init_db()

    checks = [
        ("departments", "name"),
        ("positions", "title"),
        ("employees", "full_name"),
    ]

    with connect() as conn:
        for table, column in checks:
            print("\nDB_TABLE:", table)

            rows = conn.execute(
                f"""
                SELECT company_id, {column}
                FROM {table}
                ORDER BY company_id, {column}
                """
            ).fetchall()

            if not rows:
                print("ROWS: none")
                continue

            for row in rows:
                print(row["company_id"], ascii(row[column]))


def main() -> None:
    print("=== RU DISPLAY DIAGNOSTICS ===")

    for relative_path in FILES_TO_CHECK:
        print_file_head(BASE_DIR / relative_path)

    print("\n=== DATABASE VALUES ===")
    print_database_values()


if __name__ == "__main__":
    main()