from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.db import company_exists, connect, init_db
from ot_agent.staffing_db import init_staffing_schema

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED_STAFFING_COLUMNS = [
    "schedule_id",
    "company_id",
    "row_id",
    "position_id",
    "headcount",
    "effective_date",
]

OPTIONAL_STAFFING_COLUMNS = [
    "department_id",
    "approved_date",
]

REQUIRED_JOB_COLUMNS = [
    "job_description_id",
    "company_id",
    "position_id",
    "title",
    "text_content",
]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _none_if_empty(value: Any) -> str | None:
    value = _clean(value)
    return value if value else None


def _validate_date(value: Any, entity: str, field: str, warnings: list[str]) -> str:
    value = _clean(value)
    if value and not DATE_RE.match(value):
        warnings.append(f"{entity}: field {field} is not ISO 8601: {value}")
    return value


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_staffing_csv(path: Path) -> tuple[list[dict[str, str]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, str]] = []

    if not path.exists():
        errors.append(f"File not found: {path}")
        return rows, errors, warnings

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            errors.append(f"{path.name}: empty CSV file")
            return rows, errors, warnings

        missing = [
            column
            for column in REQUIRED_STAFFING_COLUMNS
            if column not in reader.fieldnames
        ]

        if missing:
            errors.append(f"{path.name}: missing columns: {', '.join(missing)}")
            return rows, errors, warnings

        for line_no, raw_row in enumerate(reader, start=2):
            row = {key: _clean(value) for key, value in raw_row.items() if key is not None}
            row["_line_no"] = str(line_no)
            rows.append(row)

    return rows, errors, warnings


def validate_staffing_rows(
    rows: list[dict[str, str]],
    company_id: str,
    filename: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    parsed_rows: list[dict[str, Any]] = []
    schedules: dict[str, dict[str, Any]] = {}
    row_ids: set[str] = set()

    for row in rows:
        line_no = row.get("_line_no", "?")
        entity = f"{filename}, line {line_no}"

        schedule_id = row.get("schedule_id", "")
        row_company_id = row.get("company_id", "")
        row_id = row.get("row_id", "")
        department_id = row.get("department_id", "")
        position_id = row.get("position_id", "")
        headcount_raw = row.get("headcount", "")
        effective_date = _validate_date(
            row.get("effective_date", ""),
            entity,
            "effective_date",
            warnings,
        )
        approved_date = _validate_date(
            row.get("approved_date", ""),
            entity,
            "approved_date",
            warnings,
        )

        if not schedule_id:
            errors.append(f"{entity}: empty schedule_id")
        if not row_company_id:
            errors.append(f"{entity}: empty company_id")
        elif row_company_id != company_id:
            errors.append(f"{entity}: company_id={row_company_id} does not match {company_id}")
        if not row_id:
            errors.append(f"{entity}: empty row_id")
        elif row_id in row_ids:
            errors.append(f"{entity}: duplicate row_id={row_id}")
        else:
            row_ids.add(row_id)
        if not position_id:
            errors.append(f"{entity}: empty position_id")
        if not effective_date:
            errors.append(f"{entity}: empty effective_date")

        headcount: int | None = None
        if headcount_raw:
            try:
                headcount = int(headcount_raw)
                if headcount < 0:
                    errors.append(f"{entity}: headcount cannot be negative")
            except ValueError:
                errors.append(f"{entity}: headcount is not an integer: {headcount_raw}")
        else:
            errors.append(f"{entity}: empty headcount")

        if schedule_id:
            existing = schedules.get(schedule_id)

            if not existing:
                schedules[schedule_id] = {
                    "schedule_id": schedule_id,
                    "company_id": row_company_id or company_id,
                    "effective_date": effective_date,
                    "approved_date": approved_date or None,
                }
            else:
                if existing["company_id"] != row_company_id:
                    errors.append(
                        f"{entity}: schedule_id={schedule_id} has inconsistent company_id"
                    )
                if existing["effective_date"] != effective_date:
                    warnings.append(
                        f"{entity}: schedule_id={schedule_id} has inconsistent effective_date"
                    )
                if approved_date and existing.get("approved_date") and existing["approved_date"] != approved_date:
                    warnings.append(
                        f"{entity}: schedule_id={schedule_id} has inconsistent approved_date"
                    )
                if approved_date and not existing.get("approved_date"):
                    existing["approved_date"] = approved_date

        parsed_rows.append(
            {
                "row_id": row_id,
                "schedule_id": schedule_id,
                "company_id": row_company_id or company_id,
                "department_id": department_id or None,
                "position_id": position_id,
                "headcount": headcount if headcount is not None else 0,
                "effective_date": effective_date,
            }
        )

    return parsed_rows, schedules, errors, warnings


def validate_job_descriptions(
    path: Path,
    company_id: str,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    items: list[dict[str, Any]] = []

    if not path.exists():
        warnings.append(f"File not found: {path}. Job descriptions will not be imported.")
        return items, errors, warnings

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        errors.append(f"{path.name}: invalid JSON: {exc}")
        return items, errors, warnings

    if not isinstance(data, list):
        errors.append(f"{path.name}: JSON root must be a list")
        return items, errors, warnings

    ids: set[str] = set()

    for index, raw_item in enumerate(data, start=1):
        entity = f"{path.name}, item {index}"

        if not isinstance(raw_item, dict):
            errors.append(f"{entity}: item is not an object")
            continue

        item = {key: _clean(value) for key, value in raw_item.items()}

        job_description_id = item.get("job_description_id", "")
        item_company_id = item.get("company_id", "")
        position_id = item.get("position_id", "")
        title = item.get("title", "")
        text_content = item.get("text_content", "")
        source_file = item.get("source_file", "")
        version = item.get("version", "") or "v01"
        status = item.get("status", "") or "RAW"
        effective_date = _validate_date(
            item.get("effective_date", ""),
            entity,
            "effective_date",
            warnings,
        )

        missing = [
            column
            for column in REQUIRED_JOB_COLUMNS
            if not item.get(column)
        ]

        if missing:
            errors.append(f"{entity}: missing required fields: {', '.join(missing)}")
            continue

        if item_company_id != company_id:
            errors.append(f"{entity}: company_id={item_company_id} does not match {company_id}")

        if job_description_id in ids:
            errors.append(f"{entity}: duplicate job_description_id={job_description_id}")
        else:
            ids.add(job_description_id)

        items.append(
            {
                "job_description_id": job_description_id,
                "company_id": item_company_id,
                "position_id": position_id,
                "title": title,
                "source_file": source_file or None,
                "text_content": text_content,
                "version": version,
                "status": status,
                "effective_date": effective_date or None,
            }
        )

    return items, errors, warnings


def check_referential_integrity(
    parsed_rows: list[dict[str, Any]],
    job_items: list[dict[str, Any]],
    company_id: str,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    with connect() as conn:
        for row in parsed_rows:
            position_id = row.get("position_id")
            department_id = row.get("department_id")

            if position_id:
                row_company = conn.execute(
                    "SELECT company_id FROM positions WHERE position_id = ?",
                    (position_id,),
                ).fetchone()

                if not row_company:
                    errors.append(f"position not found: {position_id}")
                elif str(row_company["company_id"]) != company_id:
                    errors.append(
                        f"position {position_id} belongs to company {row_company['company_id']}, not {company_id}"
                    )

            if department_id:
                dep_company = conn.execute(
                    "SELECT company_id FROM departments WHERE department_id = ?",
                    (department_id,),
                ).fetchone()

                if not dep_company:
                    errors.append(f"department not found: {department_id}")
                elif str(dep_company["company_id"]) != company_id:
                    errors.append(
                        f"department {department_id} belongs to company {dep_company['company_id']}, not {company_id}"
                    )

        for item in job_items:
            position_id = item.get("position_id")

            if position_id:
                row_company = conn.execute(
                    "SELECT company_id FROM positions WHERE position_id = ?",
                    (position_id,),
                ).fetchone()

                if not row_company:
                    errors.append(f"job description position not found: {position_id}")
                elif str(row_company["company_id"]) != company_id:
                    errors.append(
                        f"job description position {position_id} belongs to company {row_company['company_id']}, not {company_id}"
                    )

    return errors, warnings


def check_existing_records(
    schedules: dict[str, dict[str, Any]],
    parsed_rows: list[dict[str, Any]],
    job_items: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []

    with connect() as conn:
        existing_schedules = {
            str(row["schedule_id"])
            for row in conn.execute(
                "SELECT schedule_id FROM staffing_schedules"
            ).fetchall()
        }

        existing_rows = {
            str(row["row_id"])
            for row in conn.execute(
                "SELECT row_id FROM staffing_schedule_rows"
            ).fetchall()
        }

        existing_jobs = {
            str(row["job_description_id"])
            for row in conn.execute(
                "SELECT job_description_id FROM job_descriptions"
            ).fetchall()
        }

        for schedule_id in schedules:
            if schedule_id in existing_schedules:
                errors.append(f"staffing_schedules: schedule_id={schedule_id} already exists")

        for row in parsed_rows:
            row_id = row.get("row_id")
            if row_id and row_id in existing_rows:
                errors.append(f"staffing_schedule_rows: row_id={row_id} already exists")

        for item in job_items:
            job_id = item.get("job_description_id")
            if job_id and job_id in existing_jobs:
                errors.append(f"job_descriptions: job_description_id={job_id} already exists")

    return errors


def commit_import(
    schedules: dict[str, dict[str, Any]],
    parsed_rows: list[dict[str, Any]],
    job_items: list[dict[str, Any]],
    staffing_csv_path: Path,
) -> None:
    file_hash = _file_sha256(staffing_csv_path)
    filename = staffing_csv_path.name

    with connect() as conn:
        for schedule in schedules.values():
            conn.execute(
                """
                INSERT INTO staffing_schedules (
                    schedule_id,
                    company_id,
                    approved_date,
                    effective_date,
                    filename,
                    hash,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    schedule["schedule_id"],
                    schedule["company_id"],
                    schedule.get("approved_date"),
                    schedule["effective_date"],
                    filename,
                    file_hash,
                    "ACTIVE",
                ),
            )

        for row in parsed_rows:
            conn.execute(
                """
                INSERT INTO staffing_schedule_rows (
                    row_id,
                    schedule_id,
                    company_id,
                    department_id,
                    position_id,
                    headcount
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["row_id"],
                    row["schedule_id"],
                    row["company_id"],
                    row.get("department_id"),
                    row["position_id"],
                    row["headcount"],
                ),
            )

        for item in job_items:
            conn.execute(
                """
                INSERT INTO job_descriptions (
                    job_description_id,
                    company_id,
                    position_id,
                    title,
                    source_file,
                    text_content,
                    version,
                    status,
                    effective_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["job_description_id"],
                    item["company_id"],
                    item["position_id"],
                    item["title"],
                    item.get("source_file"),
                    item["text_content"],
                    item["version"],
                    item["status"],
                    item.get("effective_date"),
                ),
            )

        conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import synthetic staffing schedules and job descriptions."
    )
    parser.add_argument("--company", required=True, help="company_id")
    parser.add_argument("--path", required=True, help="Folder with CSV and JSON files")
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Perform real database write. Without this flag, dry-run only.",
    )

    args = parser.parse_args()
    company_id = _clean(args.company)
    register_dir = (BASE_DIR / args.path).resolve()

    if not company_id:
        print("ERROR: company_id is required.")
        return 1

    init_db()
    init_staffing_schema()

    if not company_exists(company_id):
        print(f"ERROR: company {company_id} does not exist.")
        return 1

    staffing_csv_path = register_dir / "staffing_schedule.csv"
    job_json_path = register_dir / "job_descriptions.json"

    raw_staffing_rows, file_errors, file_warnings = read_staffing_csv(staffing_csv_path)

    parsed_rows, schedules, staffing_errors, staffing_warnings = validate_staffing_rows(
        raw_staffing_rows,
        company_id,
        staffing_csv_path.name,
    )

    job_items, job_errors, job_warnings = validate_job_descriptions(
        job_json_path,
        company_id,
    )

    integrity_errors, integrity_warnings = check_referential_integrity(
        parsed_rows,
        job_items,
        company_id,
    )

    all_errors = file_errors + staffing_errors + job_errors + integrity_errors
    all_warnings = file_warnings + staffing_warnings + job_warnings + integrity_warnings

    print("=== STAFFING / JOB DESCRIPTION IMPORT DIAGNOSTICS ===")
    print(f"company_id: {company_id}")
    print(f"path: {register_dir}")
    print(f"schedules: {len(schedules)}")
    print(f"schedule rows: {len(parsed_rows)}")
    print(f"job descriptions: {len(job_items)}")

    if all_warnings:
        print("\nWARNINGS:")
        for warning in all_warnings:
            print(f"- {warning}")
    else:
        print("\nWARNINGS: none")

    if all_errors:
        print("\nERRORS:")
        for error in all_errors:
            print(f"- {error}")
        print("\nImport aborted.")
        return 1

    if not args.commit:
        print("\nDRY-RUN completed successfully. No database write was performed.")
        print("Run with --commit to write data.")
        return 0

    existing_errors = check_existing_records(
        schedules,
        parsed_rows,
        job_items,
    )

    if existing_errors:
        print("\nDATABASE ERRORS:")
        for error in existing_errors:
            print(f"- {error}")
        print("\nImport aborted. Duplicates were not created.")
        return 1

    commit_import(
        schedules,
        parsed_rows,
        job_items,
        staffing_csv_path,
    )

    print("\nIMPORT COMPLETED SUCCESSFULLY.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())