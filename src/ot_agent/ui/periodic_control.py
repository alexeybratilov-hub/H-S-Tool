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
    "\u0427\u0415\u0420\u041d\u041e\u0412\u0418\u041a / \u0411\u0415\u0417 LLM. "
    "\u0414\u0435\u0442\u0435\u0440\u043c\u0438\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0439 \u043a\u043e\u043d\u0442\u0440\u043e\u043b\u044c \u0441\u0440\u043e\u043a\u043e\u0432. "
    "\u041c\u0435\u0434\u0438\u0446\u0438\u043d\u0441\u043a\u0438\u0435 \u0434\u0438\u0430\u0433\u043d\u043e\u0437\u044b \u043d\u0435 \u0445\u0440\u0430\u043d\u044f\u0442\u0441\u044f. "
    "\u041f\u0435\u0440\u0438\u043e\u0434\u0438\u0447\u043d\u043e\u0441\u0442\u044c \u043f\u043e \u0437\u0430\u043a\u043e\u043d\u0443 \u0442\u0440\u0435\u0431\u0443\u0435\u0442 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0441\u0442\u043e\u043c \u043f\u043e \u043e\u0445\u0440\u0430\u043d\u0435 \u0442\u0440\u0443\u0434\u0430."
)


def render_periodic_control() -> None:
    st.title(TITLE)
    st.warning(WARNING)

    conn = get_connection(DB_PATH)

    try:
        companies = list_companies(conn)

        if not companies:
            st.info("\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u0438 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b. \u0414\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u044e \u043d\u0430 \u0432\u043a\u043b\u0430\u0434\u043a\u0435 \u00ab\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u0438\u00bb.")
            return

        company_labels = [company["display_name"] for company in companies]
        company_ids = [company["company_id"] for company in companies]

        company_index = st.selectbox(
            "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f",
            range(len(company_labels)),
            format_func=lambda i: company_labels[i],
            key="pc_company_select",
        )

        company_id = company_ids[company_index]

        employees = list_employees(conn, company_id)

        if not employees:
            st.info("\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0438 \u044d\u0442\u043e\u0439 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b.")
            return

        employee_filter_labels = ["\u0412\u0421\u0415"] + [
            f"{employee['employee_id']} | {employee['display_name']}"
            for employee in employees
        ]

        employee_filter_index = st.selectbox(
            "\u0424\u0438\u043b\u044c\u0442\u0440 \u043f\u043e \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0443",
            range(len(employee_filter_labels)),
            format_func=lambda i: employee_filter_labels[i],
            key="pc_employee_filter",
        )

        selected_employee_id = None
        if employee_filter_index > 0:
            selected_employee_id = employees[employee_filter_index - 1]["employee_id"]

        event_type_filter = st.selectbox(
            "\u0424\u0438\u043b\u044c\u0442\u0440 \u043f\u043e \u0442\u0438\u043f\u0443 \u0441\u043e\u0431\u044b\u0442\u0438\u044f",
            ["\u0412\u0421\u0415"] + list(EVENT_TYPES),
            key="pc_event_type_filter",
        )

        status_filter = st.selectbox(
            "\u0424\u0438\u043b\u044c\u0442\u0440 \u043f\u043e \u0441\u0442\u0430\u0442\u0443\u0441\u0443",
            ["\u0412\u0421\u0415"] + list(STATUS_VALUES),
            key="pc_status_filter",
        )

        search = st.text_input("\u041f\u043e\u0438\u0441\u043a", value="", key="pc_search")

        counts = count_events_by_status(conn, company_id)

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("\u0412\u0441\u0435\u0433\u043e", counts["total"])
        c2.metric("\u0412 \u043d\u043e\u0440\u043c\u0435", counts["OK"])
        c3.metric("\u0421\u043a\u043e\u0440\u043e \u0441\u0440\u043e\u043a", counts["DUE_SOON"])
        c4.metric("\u041f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043d\u043e", counts["EXPIRED"])
        c5.metric("\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445", counts["NO_DATA"])
        c6.metric("\u041e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d", counts["RESTRICTED"])

        events = list_events(
            conn,
            company_id=company_id,
            employee_id=selected_employee_id,
            event_type=None if event_type_filter == "\u0412\u0421\u0415" else event_type_filter,
            status=None if status_filter == "\u0412\u0421\u0415" else status_filter,
            search=search.strip() if search else None,
        )

        if events:
            st.dataframe(events, hide_index=True, width="stretch")
        else:
            st.info("\u0421\u043e\u0431\u044b\u0442\u0438\u044f \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b.")

        with st.expander("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0438\u043b\u0438 \u043e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0441\u043e\u0431\u044b\u0442\u0438\u0435"):
            employee_labels = [
                f"{employee['employee_id']} | {employee['display_name']}"
                for employee in employees
            ]
            employee_ids = [employee["employee_id"] for employee in employees]

            employee_index = st.selectbox(
                "\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a",
                range(len(employee_labels)),
                format_func=lambda i: employee_labels[i],
                key="pc_form_employee",
            )

            event_type = st.selectbox(
                "\u0422\u0438\u043f \u0441\u043e\u0431\u044b\u0442\u0438\u044f",
                list(EVENT_TYPES),
                key="pc_form_event_type",
            )

            event_code = st.text_input(
                "\u041a\u043e\u0434 \u0441\u043e\u0431\u044b\u0442\u0438\u044f",
                value="\u0423\u041a\u0410\u0416\u0418\u0422\u0415_\u041a\u041e\u0414",
                key="pc_form_event_code",
            )

            performed_at = st.text_input(
                "\u0414\u0430\u0442\u0430 \u043f\u0440\u043e\u0432\u0435\u0434\u0435\u043d\u0438\u044f (\u0413\u0413\u0413\u0413-\u041c\u041c-\u0414\u0414)",
                value="",
                key="pc_form_performed_at",
            )

            valid_until = st.text_input(
                "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u0442\u0435\u043b\u0435\u043d \u0434\u043e (\u0413\u0413\u0413\u0413-\u041c\u041c-\u0414\u0414)",
                value="",
                key="pc_form_valid_until",
            )

            interval_days = st.text_input(
                "\u0418\u043d\u0442\u0435\u0440\u0432\u0430\u043b \u0432 \u0434\u043d\u044f\u0445",
                value="",
                key="pc_form_interval_days",
            )

            result_code = st.text_input(
                "\u041a\u043e\u0434 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u0430",
                value="",
                key="pc_form_result_code",
            )

            restriction_flag = st.checkbox(
                "\u0415\u0441\u0442\u044c \u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u0435",
                value=False,
                key="pc_form_restriction_flag",
            )

            reference_note = st.text_input(
                "\u0421\u0441\u044b\u043b\u043a\u0430 / \u043e\u0441\u043d\u043e\u0432\u0430\u043d\u0438\u0435",
                value="",
                key="pc_form_reference_note",
            )

            note = st.text_area(
                "\u041f\u0440\u0438\u043c\u0435\u0447\u0430\u043d\u0438\u0435",
                value="",
                key="pc_form_note",
            )

            if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u0441\u043e\u0431\u044b\u0442\u0438\u0435", key="pc_form_save_button"):
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
                    st.success("\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    finally:
        conn.close()


render = render_periodic_control
