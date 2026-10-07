from __future__ import annotations

from typing import Any

from ot_agent.db import connect

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS staffing_schedules (
    schedule_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    approved_date TEXT,
    effective_date TEXT NOT NULL,
    filename TEXT,
    hash TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS staffing_schedule_rows (
    row_id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    company_id TEXT NOT NULL,
    department_id TEXT,
    position_id TEXT NOT NULL,
    headcount INTEGER NOT NULL DEFAULT 0,
    sot_class_optional TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES staffing_schedules(schedule_id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (position_id) REFERENCES positions(position_id)
);

CREATE TABLE IF NOT EXISTS job_descriptions (
    job_description_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    position_id TEXT NOT NULL,
    title TEXT NOT NULL,
    source_file TEXT,
    text_content TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v01',
    status TEXT NOT NULL DEFAULT 'RAW',
    effective_date TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id) ON DELETE CASCADE,
    FOREIGN KEY (position_id) REFERENCES positions(position_id)
);

CREATE INDEX IF NOT EXISTS idx_staffing_schedules_company_id
    ON staffing_schedules(company_id);

CREATE INDEX IF NOT EXISTS idx_staffing_schedule_rows_company_id
    ON staffing_schedule_rows(company_id);

CREATE INDEX IF NOT EXISTS idx_staffing_schedule_rows_schedule_id
    ON staffing_schedule_rows(schedule_id);

CREATE INDEX IF NOT EXISTS idx_job_descriptions_company_id
    ON job_descriptions(company_id);

CREATE INDEX IF NOT EXISTS idx_job_descriptions_position_id
    ON job_descriptions(position_id);
"""


def _clean(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

    return value


def init_staffing_schema() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def staffing_schedule_exists(schedule_id: str) -> bool:
    schedule_id = _clean(schedule_id)

    if not schedule_id:
        return False

    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM staffing_schedules WHERE schedule_id = ?",
            (str(schedule_id),),
        ).fetchone()

        return row is not None


def staffing_row_exists(row_id: str) -> bool:
    row_id = _clean(row_id)

    if not row_id:
        return False

    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM staffing_schedule_rows WHERE row_id = ?",
            (str(row_id),),
        ).fetchone()

        return row is not None


def job_description_exists(job_description_id: str) -> bool:
    job_description_id = _clean(job_description_id)

    if not job_description_id:
        return False

    with connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM job_descriptions WHERE job_description_id = ?",
            (str(job_description_id),),
        ).fetchone()

        return row is not None


def get_position_company(conn, position_id: str) -> str | None:
    position_id = _clean(position_id)

    if not position_id:
        return None

    row = conn.execute(
        "SELECT company_id FROM positions WHERE position_id = ?",
        (str(position_id),),
    ).fetchone()

    return str(row["company_id"]) if row else None


def get_department_company(conn, department_id: str) -> str | None:
    department_id = _clean(department_id)

    if not department_id:
        return None

    row = conn.execute(
        "SELECT company_id FROM departments WHERE department_id = ?",
        (str(department_id),),
    ).fetchone()

    return str(row["company_id"]) if row else None


def create_staffing_schedule(data: dict[str, Any]) -> None:
    schedule_id = _clean(data.get("schedule_id"))
    company_id = _clean(data.get("company_id"))
    effective_date = _clean(data.get("effective_date"))

    if not schedule_id:
        raise ValueError("Поле schedule_id обязательно.")

    if not company_id:
        raise ValueError("Поле company_id обязательно.")

    if not effective_date:
        raise ValueError("Поле effective_date обязательно.")

    payload = (
        str(schedule_id),
        str(company_id),
        _clean(data.get("approved_date")),
        str(effective_date),
        _clean(data.get("filename")),
        _clean(data.get("hash")),
        _clean(data.get("status")) or "ACTIVE",
    )

    with connect() as conn:
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
            payload,
        )
        conn.commit()


def add_staffing_schedule_row(data: dict[str, Any]) -> None:
    row_id = _clean(data.get("row_id"))
    schedule_id = _clean(data.get("schedule_id"))
    company_id = _clean(data.get("company_id"))
    position_id = _clean(data.get("position_id"))
    headcount = data.get("headcount")

    if not row_id:
        raise ValueError("Поле row_id обязательно.")

    if not schedule_id:
        raise ValueError("Поле schedule_id обязательно.")

    if not company_id:
        raise ValueError("Поле company_id обязательно.")

    if not position_id:
        raise ValueError("Поле position_id обязательно.")

    if headcount is None:
        raise ValueError("Поле headcount обязательно.")

    headcount = int(headcount)

    department_id = _clean(data.get("department_id"))
    sot_class_optional = _clean(data.get("sot_class_optional"))

    with connect() as conn:
        schedule = conn.execute(
            "SELECT company_id FROM staffing_schedules WHERE schedule_id = ?",
            (str(schedule_id),),
        ).fetchone()

        if not schedule:
            raise ValueError(f"Штатное расписание не найдено: {schedule_id}")

        if str(schedule["company_id"]) != str(company_id):
            raise ValueError(
                f"Штатное расписание {schedule_id} принадлежит другой компании."
            )

        position_company = get_position_company(conn, str(position_id))

        if not position_company:
            raise ValueError(f"Должность не найдена: {position_id}")

        if position_company != str(company_id):
            raise ValueError(
                f"Должность {position_id} принадлежит другой компании."
            )

        if department_id:
            department_company = get_department_company(conn, str(department_id))

            if not department_company:
                raise ValueError(f"Подразделение не найдено: {department_id}")

            if department_company != str(company_id):
                raise ValueError(
                    f"Подразделение {department_id} принадлежит другой компании."
                )

        conn.execute(
            """
            INSERT INTO staffing_schedule_rows (
                row_id,
                schedule_id,
                company_id,
                department_id,
                position_id,
                headcount,
                sot_class_optional
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(row_id),
                str(schedule_id),
                str(company_id),
                str(department_id) if department_id else None,
                str(position_id),
                headcount,
                str(sot_class_optional) if sot_class_optional else None,
            ),
        )
        conn.commit()


def add_job_description(data: dict[str, Any]) -> None:
    job_description_id = _clean(data.get("job_description_id"))
    company_id = _clean(data.get("company_id"))
    position_id = _clean(data.get("position_id"))
    title = _clean(data.get("title"))
    text_content = _clean(data.get("text_content"))

    if not job_description_id:
        raise ValueError("Поле job_description_id обязательно.")

    if not company_id:
        raise ValueError("Поле company_id обязательно.")

    if not position_id:
        raise ValueError("Поле position_id обязательно.")

    if not title:
        raise ValueError("Поле title обязательно.")

    if not text_content:
        raise ValueError("Поле text_content обязательно.")

    source_file = _clean(data.get("source_file"))
    version = _clean(data.get("version")) or "v01"
    status = _clean(data.get("status")) or "RAW"
    effective_date = _clean(data.get("effective_date"))

    with connect() as conn:
        position_company = get_position_company(conn, str(position_id))

        if not position_company:
            raise ValueError(f"Должность не найдена: {position_id}")

        if position_company != str(company_id):
            raise ValueError(
                f"Должность {position_id} принадлежит другой компании."
            )

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
                str(job_description_id),
                str(company_id),
                str(position_id),
                str(title),
                str(source_file) if source_file else None,
                str(text_content),
                str(version),
                str(status),
                str(effective_date) if effective_date else None,
            ),
        )
        conn.commit()


def list_staffing_schedules(company_id: str) -> list[dict[str, Any]]:
    company_id = _clean(company_id)

    if not company_id:
        return []

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM staffing_schedules
            WHERE company_id = ?
            ORDER BY effective_date DESC, schedule_id
            """,
            (str(company_id),),
        ).fetchall()

        return [dict(row) for row in rows]


def list_staffing_schedule_rows(company_id: str) -> list[dict[str, Any]]:
    company_id = _clean(company_id)

    if not company_id:
        return []

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                r.row_id,
                r.schedule_id,
                r.company_id,
                r.department_id,
                dep.name AS department_name,
                r.position_id,
                pos.title AS position_title,
                r.headcount,
                r.sot_class_optional,
                s.effective_date,
                s.approved_date,
                s.status AS schedule_status,
                s.filename,
                s.hash
            FROM staffing_schedule_rows r
            JOIN staffing_schedules s
                ON s.schedule_id = r.schedule_id
                AND s.company_id = r.company_id
            LEFT JOIN positions pos
                ON pos.position_id = r.position_id
                AND pos.company_id = r.company_id
            LEFT JOIN departments dep
                ON dep.department_id = r.department_id
                AND dep.company_id = r.company_id
            WHERE r.company_id = ?
            ORDER BY s.effective_date DESC, r.row_id
            """,
            (str(company_id),),
        ).fetchall()

        return [dict(row) for row in rows]


def list_job_descriptions(company_id: str) -> list[dict[str, Any]]:
    company_id = _clean(company_id)

    if not company_id:
        return []

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                jd.job_description_id,
                jd.company_id,
                jd.position_id,
                pos.title AS position_title,
                jd.title,
                jd.source_file,
                jd.text_content,
                jd.version,
                jd.status,
                jd.effective_date,
                jd.created_at,
                jd.updated_at
            FROM job_descriptions jd
            LEFT JOIN positions pos
                ON pos.position_id = jd.position_id
                AND pos.company_id = jd.company_id
            WHERE jd.company_id = ?
            ORDER BY jd.title
            """,
            (str(company_id),),
        ).fetchall()

        return [dict(row) for row in rows]


def count_staffing(company_id: str) -> dict[str, int]:
    company_id = _clean(company_id)

    if not company_id:
        return {
            "schedules": 0,
            "schedule_rows": 0,
            "job_descriptions": 0,
        }

    with connect() as conn:
        schedules = conn.execute(
            "SELECT COUNT(*) FROM staffing_schedules WHERE company_id = ?",
            (str(company_id),),
        ).fetchone()[0]

        schedule_rows = conn.execute(
            "SELECT COUNT(*) FROM staffing_schedule_rows WHERE company_id = ?",
            (str(company_id),),
        ).fetchone()[0]

        job_descriptions = conn.execute(
            "SELECT COUNT(*) FROM job_descriptions WHERE company_id = ?",
            (str(company_id),),
        ).fetchone()[0]

    return {
        "schedules": int(schedules),
        "schedule_rows": int(schedule_rows),
        "job_descriptions": int(job_descriptions),
    }