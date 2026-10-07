from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.db import company_exists, connect, init_db

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

DEPARTMENT_COLUMNS = [
    "department_id",
    "company_id",
    "name",
    "parent_department_id",
    "responsible_employee_id",
    "status",
]

POSITION_COLUMNS = [
    "position_id",
    "company_id",
    "title",
    "department_id",
    "headcount",
    "effective_from",
    "status",
]

EMPLOYEE_COLUMNS = [
    "employee_id",
    "company_id",
    "full_name",
    "personnel_number",
    "position_id",
    "department_id",
    "hire_date",
    "status",
]

DEPARTMENT_INSERT_COLUMNS = [
    "department_id",
    "company_id",
    "name",
    "parent_department_id",
    "responsible_employee_id",
    "status",
]

POSITION_INSERT_COLUMNS = [
    "position_id",
    "company_id",
    "title",
    "department_id",
    "headcount",
    "effective_from",
    "status",
]

EMPLOYEE_INSERT_COLUMNS = [
    "employee_id",
    "company_id",
    "full_name",
    "personnel_number",
    "position_id",
    "department_id",
    "hire_date",
    "status",
]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _none_if_empty(value: Any) -> str | None:
    value = _clean(value)
    return value if value else None


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    df.columns = [_clean(column) for column in df.columns]
    return df.fillna("")


def _missing_columns(df: pd.DataFrame, columns: list[str], filename: str) -> list[str]:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        return [f"{filename}: отсутствуют колонки: {', '.join(missing)}"]
    return []


def _optional_int(value: Any) -> int | None:
    value = _clean(value)
    if not value:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def _validate_date(value: Any, entity: str, field: str, warnings: list[str]) -> str:
    value = _clean(value)
    if value and not DATE_RE.match(value):
        warnings.append(f"{entity}: поле {field} не соответствует ISO 8601: {value}")
    return value


def validate_departments(
    df: pd.DataFrame,
    company_id: str,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    filename = "departments.csv"
    errors = _missing_columns(df, DEPARTMENT_COLUMNS, filename)
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()

    for index, row in df.iterrows():
        line = index + 2

        department_id = _clean(row.get("department_id"))
        row_company_id = _clean(row.get("company_id"))
        name = _clean(row.get("name"))
        parent_department_id = _clean(row.get("parent_department_id"))
        responsible_employee_id = _clean(row.get("responsible_employee_id"))
        status = _clean(row.get("status")) or "ACTIVE"

        if not department_id:
            errors.append(f"{filename}, строка {line}: пустой department_id")
        elif department_id in ids:
            errors.append(f"{filename}, строка {line}: дубликат department_id={department_id}")
        else:
            ids.add(department_id)

        if row_company_id != company_id:
            errors.append(
                f"{filename}, строка {line}: company_id={row_company_id} не равен {company_id}"
            )

        if not name:
            errors.append(f"{filename}, строка {line}: пустое наименование подразделения")

        if status not in {"ACTIVE", "INACTIVE", "ARCHIVED"}:
            warnings.append(f"{filename}, строка {line}: нестандартный статус {status}")

        rows.append(
            {
                "department_id": department_id,
                "company_id": row_company_id,
                "name": name,
                "parent_department_id": _none_if_empty(parent_department_id),
                "responsible_employee_id": _none_if_empty(responsible_employee_id),
                "status": status,
            }
        )

    for row in rows:
        parent = row["parent_department_id"]
        if parent and parent not in ids:
            errors.append(
                f"{filename}: parent_department_id={parent} не найден в departments.csv"
            )

    return errors, warnings, rows


def validate_positions(
    df: pd.DataFrame,
    company_id: str,
    department_ids: set[str],
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    filename = "positions.csv"
    errors = _missing_columns(df, POSITION_COLUMNS, filename)
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()

    for index, row in df.iterrows():
        line = index + 2

        position_id = _clean(row.get("position_id"))
        row_company_id = _clean(row.get("company_id"))
        title = _clean(row.get("title"))
        department_id = _clean(row.get("department_id"))
        headcount_raw = _clean(row.get("headcount"))
        headcount = _optional_int(headcount_raw)
        effective_from = _validate_date(
            row.get("effective_from"),
            f"{filename}, строка {line}",
            "effective_from",
            warnings,
        )
        status = _clean(row.get("status")) or "ACTIVE"

        if not position_id:
            errors.append(f"{filename}, строка {line}: пустой position_id")
        elif position_id in ids:
            errors.append(f"{filename}, строка {line}: дубликат position_id={position_id}")
        else:
            ids.add(position_id)

        if row_company_id != company_id:
            errors.append(
                f"{filename}, строка {line}: company_id={row_company_id} не равен {company_id}"
            )

        if not title:
            errors.append(f"{filename}, строка {line}: пустое наименование должности")

        if not department_id:
            warnings.append(f"{filename}, строка {line}: должность не привязана к подразделению")
        elif department_id not in department_ids:
            errors.append(
                f"{filename}, строка {line}: department_id={department_id} не найден в departments.csv"
            )

        if headcount_raw and headcount is None:
            warnings.append(f"{filename}, строка {line}: headcount не является числом: {headcount_raw}")

        if status not in {"ACTIVE", "INACTIVE", "ARCHIVED"}:
            warnings.append(f"{filename}, строка {line}: нестандартный статус {status}")

        rows.append(
            {
                "position_id": position_id,
                "company_id": row_company_id,
                "title": title,
                "department_id": _none_if_empty(department_id),
                "headcount": headcount,
                "effective_from": _none_if_empty(effective_from),
                "status": status,
            }
        )

    return errors, warnings, rows


def validate_employees(
    df: pd.DataFrame,
    company_id: str,
    department_ids: set[str],
    position_ids: set[str],
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    filename = "employees.csv"
    errors = _missing_columns(df, EMPLOYEE_COLUMNS, filename)
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    personnel_numbers: set[str] = set()

    for index, row in df.iterrows():
        line = index + 2

        employee_id = _clean(row.get("employee_id"))
        row_company_id = _clean(row.get("company_id"))
        full_name = _clean(row.get("full_name"))
        personnel_number = _clean(row.get("personnel_number"))
        position_id = _clean(row.get("position_id"))
        department_id = _clean(row.get("department_id"))
        hire_date = _validate_date(
            row.get("hire_date"),
            f"{filename}, строка {line}",
            "hire_date",
            warnings,
        )
        status = _clean(row.get("status")) or "ACTIVE"

        if not employee_id:
            errors.append(f"{filename}, строка {line}: пустой employee_id")
        elif employee_id in ids:
            errors.append(f"{filename}, строка {line}: дубликат employee_id={employee_id}")
        else:
            ids.add(employee_id)

        if row_company_id != company_id:
            errors.append(
                f"{filename}, строка {line}: company_id={row_company_id} не равен {company_id}"
            )

        if not full_name:
            errors.append(f"{filename}, строка {line}: пустой full_name")

        if personnel_number:
            if personnel_number in personnel_numbers:
                errors.append(
                    f"{filename}, строка {line}: дубликат personnel_number={personnel_number}"
                )
            else:
                personnel_numbers.add(personnel_number)
        else:
            warnings.append(f"{filename}, строка {line}: пустой personnel_number")

        if not position_id:
            errors.append(f"{filename}, строка {line}: пустой position_id")
        elif position_id not in position_ids:
            errors.append(
                f"{filename}, строка {line}: position_id={position_id} не найден в positions.csv"
            )

        if not department_id:
            errors.append(f"{filename}, строка {line}: пустой department_id")
        elif department_id not in department_ids:
            errors.append(
                f"{filename}, строка {line}: department_id={department_id} не найден в departments.csv"
            )

        if status not in {"ACTIVE", "INACTIVE", "ARCHIVED", "TERMINATED"}:
            warnings.append(f"{filename}, строка {line}: нестандартный статус {status}")

        rows.append(
            {
                "employee_id": employee_id,
                "company_id": row_company_id,
                "full_name": full_name,
                "personnel_number": _none_if_empty(personnel_number),
                "position_id": _none_if_empty(position_id),
                "department_id": _none_if_empty(department_id),
                "hire_date": _none_if_empty(hire_date),
                "status": status,
            }
        )

    return errors, warnings, rows


def _existing_ids(conn, table: str, id_column: str, company_id: str) -> set[str]:
    rows = conn.execute(
        f"SELECT {id_column} FROM {table} WHERE company_id = ?",
        (company_id,),
    ).fetchall()

    return {str(row[id_column]) for row in rows}


def check_existing_records(
    conn,
    company_id: str,
    departments: list[dict[str, Any]],
    positions: list[dict[str, Any]],
    employees: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []

    existing_departments = _existing_ids(conn, "departments", "department_id", company_id)
    existing_positions = _existing_ids(conn, "positions", "position_id", company_id)
    existing_employees = _existing_ids(conn, "employees", "employee_id", company_id)

    for row in departments:
        if row["department_id"] in existing_departments:
            errors.append(
                f"departments: department_id={row['department_id']} уже существует в базе данных"
            )

    for row in positions:
        if row["position_id"] in existing_positions:
            errors.append(
                f"positions: position_id={row['position_id']} уже существует в базе данных"
            )

    for row in employees:
        if row["employee_id"] in existing_employees:
            errors.append(
                f"employees: employee_id={row['employee_id']} уже существует в базе данных"
            )

    return errors


def _insert_rows(conn, table: str, columns: list[str], rows: list[dict[str, Any]]) -> None:
    for row in rows:
        values = tuple(row[column] for column in columns)
        placeholders = ", ".join(["?"] * len(columns))
        column_list = ", ".join(columns)

        sql = f"INSERT INTO {table} ({column_list}) VALUES ({placeholders})"
        conn.execute(sql, values)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Импорт синтетических реестров LLC_TEST_ALPHA в SQLite."
    )
    parser.add_argument(
        "--company",
        default="LLC_TEST_ALPHA",
        help="company_id для импорта.",
    )
    parser.add_argument(
        "--path",
        default="06_TESTS/synthetic_registers/LLC_TEST_ALPHA",
        help="Папка с CSV-файлами.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Выполнить реальную запись в базу. Без этого флага работает dry-run.",
    )

    args = parser.parse_args()
    company_id = _clean(args.company)
    register_dir = (BASE_DIR / args.path).resolve()

    if not company_id:
        print("ОШИБКА: не задан company_id.")
        return 1

    init_db()

    if not company_exists(company_id):
        print(f"ОШИБКА: компания {company_id} не найдена в базе данных.")
        print("Сначала создайте компанию в разделе Companies.")
        return 1

    try:
        departments_df = _read_csv(register_dir / "departments.csv")
        positions_df = _read_csv(register_dir / "positions.csv")
        employees_df = _read_csv(register_dir / "employees.csv")
    except FileNotFoundError as exc:
        print(f"ОШИБКА: {exc}")
        return 1

    department_errors, department_warnings, department_rows = validate_departments(
        departments_df,
        company_id,
    )

    department_ids = {row["department_id"] for row in department_rows if row["department_id"]}

    position_errors, position_warnings, position_rows = validate_positions(
        positions_df,
        company_id,
        department_ids,
    )

    position_ids = {row["position_id"] for row in position_rows if row["position_id"]}

    employee_errors, employee_warnings, employee_rows = validate_employees(
        employees_df,
        company_id,
        department_ids,
        position_ids,
    )

    employee_ids = {row["employee_id"] for row in employee_rows if row["employee_id"]}

    for row in department_rows:
        responsible = row["responsible_employee_id"]
        if responsible and responsible not in employee_ids:
            department_warnings.append(
                f"departments.csv: responsible_employee_id={responsible} не найден в employees.csv"
            )

    all_errors = department_errors + position_errors + employee_errors
    all_warnings = department_warnings + position_warnings + employee_warnings

    print("=== ДИАГНОСТИКА ИМПОРТА ===")
    print(f"company_id: {company_id}")
    print(f"Папка: {register_dir}")
    print(f"Подразделения: {len(department_rows)}")
    print(f"Должности: {len(position_rows)}")
    print(f"Сотрудники: {len(employee_rows)}")

    if all_warnings:
        print("\nПРЕДУПРЕЖДЕНИЯ:")
        for warning in all_warnings:
            print(f"- {warning}")
    else:
        print("\nПРЕДУПРЕЖДЕНИЙ НЕТ.")

    if all_errors:
        print("\nОШИБКИ:")
        for error in all_errors:
            print(f"- {error}")
        print("\nИмпорт невозможен. Исправьте CSV-файлы.")
        return 1

    if not args.commit:
        print("\nDRY-RUN завершён успешно. Реальная запись в базу не выполнялась.")
        print("Для записи выполните команду с флагом --commit.")
        return 0

    with connect() as conn:
        existing_errors = check_existing_records(
            conn,
            company_id,
            department_rows,
            position_rows,
            employee_rows,
        )

        if existing_errors:
            print("\nОШИБКИ БАЗЫ ДАННЫХ:")
            for error in existing_errors:
                print(f"- {error}")
            print("\nЗапись отменена. Дубликаты не создавались.")
            return 1

        _insert_rows(conn, "departments", DEPARTMENT_INSERT_COLUMNS, department_rows)
        _insert_rows(conn, "positions", POSITION_INSERT_COLUMNS, position_rows)
        _insert_rows(conn, "employees", EMPLOYEE_INSERT_COLUMNS, employee_rows)

        conn.commit()

    print("\nИМПОРТ ВЫПОЛНЕН УСПЕШНО.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())