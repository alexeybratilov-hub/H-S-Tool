from __future__ import annotations

import pandas as pd
import streamlit as st

from ot_agent.staffing_db import (
    count_staffing,
    list_job_descriptions,
    list_staffing_schedule_rows,
    list_staffing_schedules,
)
from ot_agent.ui.common import render_company_selector


def _rows_to_dataframe(
    rows: list[dict[str, object]],
    columns: list[str],
) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=columns)

    cleaned_rows = []

    for row in rows:
        cleaned = {}

        for column in columns:
            value = row.get(column)

            if value is None:
                cleaned[column] = ""
            else:
                cleaned[column] = str(value)

        cleaned_rows.append(cleaned)

    return pd.DataFrame(cleaned_rows, columns=columns)


def render() -> None:
    st.subheader("\u0428\u0442\u0430\u0442\u043d\u043e\u0435 \u0440\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435")

    company_id = render_company_selector(key="staffing_company_selector")

    if not company_id:
        return

    counts = count_staffing(company_id)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "\u0428\u0442\u0430\u0442\u043d\u044b\u0435 \u0440\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u044f",
        counts.get("schedules", 0),
    )

    col2.metric(
        "\u0421\u0442\u0440\u043e\u043a\u0438",
        counts.get("schedule_rows", 0),
    )

    col3.metric(
        "\u0418\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u0438",
        counts.get("job_descriptions", 0),
    )

    st.caption(
        "\u041e\u0442\u043e\u0431\u0440\u0430\u0436\u0430\u044e\u0442\u0441\u044f "
        "\u0442\u043e\u043b\u044c\u043a\u043e \u0434\u0430\u043d\u043d\u044b\u0435 "
        "\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438: "
        f"{company_id}"
    )

    schedule_label = "\u0428\u0442\u0430\u0442\u043d\u043e\u0435 \u0440\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435"
    job_label = "\u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u043d\u044b\u0435 \u0438\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u0438"

    tab_schedule, tab_jobs = st.tabs([schedule_label, job_label])

    with tab_schedule:
        schedules = list_staffing_schedules(company_id)
        rows = list_staffing_schedule_rows(company_id)

        if not schedules:
            st.info("\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445")
        else:
            st.markdown("#### Schedules")
            schedule_columns = [
                "schedule_id",
                "company_id",
                "effective_date",
                "approved_date",
                "status",
                "filename",
                "hash",
            ]
            st.dataframe(
                _rows_to_dataframe(schedules, schedule_columns),
                hide_index=True,
                width="stretch",
            )

            st.markdown("#### Rows")
            row_columns = [
                "row_id",
                "schedule_id",
                "department_id",
                "department_name",
                "position_id",
                "position_title",
                "headcount",
                "effective_date",
                "approved_date",
                "schedule_status",
            ]
            st.dataframe(
                _rows_to_dataframe(rows, row_columns),
                hide_index=True,
                width="stretch",
            )

    with tab_jobs:
        jobs = list_job_descriptions(company_id)

        if not jobs:
            st.info("\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445")
        else:
            columns = [
                "job_description_id",
                "title",
                "position_id",
                "position_title",
                "version",
                "status",
                "effective_date",
                "source_file",
                "text_content",
            ]
            st.dataframe(
                _rows_to_dataframe(jobs, columns),
                hide_index=True,
                width="stretch",
            )