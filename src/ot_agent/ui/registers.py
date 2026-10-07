from __future__ import annotations

import pandas as pd
import streamlit as st

from ot_agent.db import (
    count_registers,
    list_departments,
    list_employees,
    list_positions,
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
    st.subheader("Registers")

    company_id = render_company_selector(key="registers_company_selector")

    if not company_id:
        return

    counts = count_registers(company_id)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "\u041f\u043e\u0434\u0440\u0430\u0437\u0434\u0435\u043b\u0435\u043d\u0438\u044f",
        counts.get("departments", 0),
    )

    col2.metric(
        "\u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u0438",
        counts.get("positions", 0),
    )

    col3.metric(
        "\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0438",
        counts.get("employees", 0),
    )

    st.caption(
        "\u041e\u0442\u043e\u0431\u0440\u0430\u0436\u0430\u044e\u0442\u0441\u044f "
        "\u0442\u043e\u043b\u044c\u043a\u043e \u0434\u0430\u043d\u043d\u044b\u0435 "
        "\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438: "
        f"{company_id}"
    )

    tab_departments, tab_positions, tab_employees = st.tabs(
        [
            "\u041f\u043e\u0434\u0440\u0430\u0437\u0434\u0435\u043b\u0435\u043d\u0438\u044f",
            "\u0414\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u0438",
            "\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0438",
        ]
    )

    with tab_departments:
        rows = list_departments(company_id)
        columns = [
            "department_id",
            "name",
            "parent_department_id",
            "parent_department_name",
            "responsible_employee_id",
            "responsible_employee_name",
            "status",
        ]
        st.dataframe(
            _rows_to_dataframe(rows, columns),
            hide_index=True,
            width="stretch",
        )

    with tab_positions:
        rows = list_positions(company_id)
        columns = [
            "position_id",
            "title",
            "department_id",
            "department_name",
            "headcount",
            "effective_from",
            "effective_to",
            "status",
        ]
        st.dataframe(
            _rows_to_dataframe(rows, columns),
            hide_index=True,
            width="stretch",
        )

    with tab_employees:
        rows = list_employees(company_id)
        columns = [
            "employee_id",
            "full_name",
            "personnel_number",
            "position_id",
            "position_title",
            "department_id",
            "department_name",
            "hire_date",
            "termination_date",
            "status",
            "comment",
        ]
        st.dataframe(
            _rows_to_dataframe(rows, columns),
            hide_index=True,
            width="stretch",
        )