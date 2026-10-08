import streamlit as st
from pathlib import Path

from ot_agent.periodic_control_db import (
    EVENT_TYPES,
    STATUS_VALUES,
    count_events_by_status,
    get_connection,
    list_companies,
    list_employees,
    list_events,
    upsert_event,
)

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

TITLE = "\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c \u0441\u0440\u043e\u043a\u043e\u0432"

WARNING = (
    "DRAFT / NO_LLM. "
    "Synthetic deterministic deadline control. "
    "Medical diagnoses are not stored. "
    "Legal periodicity requires verification by an occupational safety specialist."
)


def render_periodic_control() -> None:
    st.title(TITLE)
    st.warning(WARNING)

    conn = get_connection(DB_PATH)

    try:
        companies = list_companies(conn)

        if not companies:
            st.info("No companies found.")
            return

        company_labels = [company["display_name"] for company in companies]
        company_ids = [company["company_id"] for company in companies]

        company_index = st.selectbox(
            "Company",
            range(len(company_labels)),
            format_func=lambda i: company_labels[i],
            key="pc_company_select",
        )

        company_id = company_ids[company_index]

        employees = list_employees(conn, company_id)

        if not employees:
            st.info("No employees found for this company.")
            return

        employee_filter_labels = ["ALL"] + [
            f"{employee['employee_id']} | {employee['display_name']}"
            for employee in employees
        ]

        employee_filter_index = st.selectbox(
            "Employee filter",
            range(len(employee_filter_labels)),
            format_func=lambda i: employee_filter_labels[i],
            key="pc_employee_filter",
        )

        selected_employee_id = None
        if employee_filter_index > 0:
            selected_employee_id = employees[employee_filter_index - 1]["employee_id"]

        event_type_filter = st.selectbox(
            "Event type filter",
            ["ALL"] + list(EVENT_TYPES),
            key="pc_event_type_filter",
        )

        status_filter = st.selectbox(
            "Status filter",
            ["ALL"] + list(STATUS_VALUES),
            key="pc_status_filter",
        )

        search = st.text_input("Search", value="", key="pc_search")

        counts = count_events_by_status(conn, company_id)

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Total", counts["total"])
        c2.metric("OK", counts["OK"])
        c3.metric("DUE_SOON", counts["DUE_SOON"])
        c4.metric("EXPIRED", counts["EXPIRED"])
        c5.metric("NO_DATA", counts["NO_DATA"])
        c6.metric("RESTRICTED", counts["RESTRICTED"])

        events = list_events(
            conn,
            company_id=company_id,
            employee_id=selected_employee_id,
            event_type=None if event_type_filter == "ALL" else event_type_filter,
            status=None if status_filter == "ALL" else status_filter,
            search=search.strip() if search else None,
        )

        if events:
            st.dataframe(events, hide_index=True, width="stretch")
        else:
            st.info("No events found.")

        with st.expander("Add or update event"):
            employee_labels = [
                f"{employee['employee_id']} | {employee['display_name']}"
                for employee in employees
            ]
            employee_ids = [employee["employee_id"] for employee in employees]

            employee_index = st.selectbox(
                "Employee",
                range(len(employee_labels)),
                format_func=lambda i: employee_labels[i],
                key="pc_form_employee",
            )

            event_type = st.selectbox(
                "Event type",
                list(EVENT_TYPES),
                key="pc_form_event_type",
            )

            event_code = st.text_input(
                "Event code",
                value="SYNTHETIC",
                key="pc_form_event_code",
            )

            performed_at = st.text_input(
                "Performed at (YYYY-MM-DD)",
                value="",
                key="pc_form_performed_at",
            )

            valid_until = st.text_input(
                "Valid until (YYYY-MM-DD)",
                value="",
                key="pc_form_valid_until",
            )

            interval_days = st.text_input(
                "Interval days",
                value="",
                key="pc_form_interval_days",
            )

            result_code = st.text_input(
                "Result code",
                value="",
                key="pc_form_result_code",
            )

            restriction_flag = st.checkbox(
                "Restricted",
                value=False,
                key="pc_form_restriction_flag",
            )

            reference_note = st.text_input(
                "Reference note",
                value="",
                key="pc_form_reference_note",
            )

            note = st.text_area(
                "Note",
                value="",
                key="pc_form_note",
            )

            if st.button("Save event", key="pc_form_save_button"):
                try:
                    upsert_event(
                        conn,
                        company_id=company_id,
                        employee_id=employee_ids[employee_index],
                        event_type=event_type,
                        event_code=event_code.strip(),
                        performed_at=performed_at.strip() or None,
                        valid_until=valid_until.strip() or None,
                        interval_days=interval_days.strip() or None,
                        result_code=result_code.strip() or None,
                        restriction_flag=1 if restriction_flag else 0,
                        reference_note=reference_note.strip() or None,
                        note=note.strip() or None,
                    )
                    conn.commit()
                    st.success("Saved.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    finally:
        conn.close()


render = render_periodic_control
