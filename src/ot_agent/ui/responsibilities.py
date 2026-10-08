import streamlit as st
from pathlib import Path

from ot_agent.responsibility_db import (
    count_assignments_by_status,
    get_connection,
    list_assignments,
    list_companies,
    list_employees,
    list_roles,
    upsert_assignment,
)

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

STATUS_OPTIONS = [
    "PROPOSED",
    "CONFIRMED",
    "MISSING_EVIDENCE",
    "REQUIRES_VERIFICATION",
    "REJECTED",
]


def render_responsibilities() -> None:
    st.title(
        "\u0427\u0435\u043a\u043b\u0438\u0441\u0442 "
        "\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0445"
    )

    st.warning(
        "DRAFT / REQUIRES_VERIFICATION. "
        "\u0421\u0438\u043d\u0442\u0435\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0439 "
        "\u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0439 "
        "\u0447\u0435\u043a\u043b\u0438\u0441\u0442. "
        "\u041d\u0435 \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u0438\u0439 "
        "\u0440\u0435\u0435\u0441\u0442\u0440. "
        "\u041a\u043e\u0434\u044b \u0440\u043e\u043b\u0435\u0439 "
        "\u044f\u0432\u043b\u044f\u044e\u0442\u0441\u044f "
        "\u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u043c\u0438 "
        "\u0438\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u0430\u043c\u0438 "
        "\u0438 \u0442\u0440\u0435\u0431\u0443\u044e\u0442 "
        "\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438."
    )

    conn = get_connection(DB_PATH)

    try:
        companies = list_companies(conn)

        if not companies:
            st.info(
                "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u0438 "
                "\u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b."
            )
            return

        company_labels = [
            company["display_name"]
            for company in companies
        ]
        company_ids = [
            company["company_id"]
            for company in companies
        ]

        company_index = st.selectbox(
            "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f",
            range(len(company_labels)),
            format_func=lambda i: company_labels[i],
        )

        company_id = company_ids[company_index]

        counts = count_assignments_by_status(conn, company_id)

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric(
            "\u0412\u0441\u0435\u0433\u043e",
            counts["total"],
        )
        c2.metric("PROPOSED", counts["PROPOSED"])
        c3.metric("CONFIRMED", counts["CONFIRMED"])
        c4.metric("MISSING_EVIDENCE", counts["MISSING_EVIDENCE"])
        c5.metric("REQUIRES_VERIFICATION", counts["REQUIRES_VERIFICATION"])
        c6.metric("REJECTED", counts["REJECTED"])

        assignments = list_assignments(conn, company_id)

        if assignments:
            st.dataframe(assignments, hide_index=True, width="stretch")
        else:
            st.info(
                "\u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f "
                "\u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b."
            )

        with st.expander(
            "\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c "
            "\u0438\u043b\u0438 \u043e\u0431\u043d\u043e\u0432\u0438\u0442\u044c "
            "\u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435"
        ):
            roles = list_roles(conn)
            employees = list_employees(conn, company_id)

            if not roles:
                st.info(
                    "\u0420\u043e\u043b\u0438 "
                    "\u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b."
                )
            elif not employees:
                st.info(
                    "\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0438 "
                    "\u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b "
                    "\u0434\u043b\u044f \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u043e\u0439 "
                    "\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438."
                )
            else:
                role_labels = [
                    f"{role['code']} | {role['title']}"
                    for role in roles
                ]
                role_ids = [
                    role["role_id"]
                    for role in roles
                ]

                employee_labels = [
                    f"{employee['employee_id']} | {employee['display_name']}"
                    for employee in employees
                ]
                employee_ids = [
                    employee["employee_id"]
                    for employee in employees
                ]

                role_index = st.selectbox(
                    "\u0420\u043e\u043b\u044c",
                    range(len(role_labels)),
                    format_func=lambda i: role_labels[i],
                )

                employee_index = st.selectbox(
                    "\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a",
                    range(len(employee_labels)),
                    format_func=lambda i: employee_labels[i],
                )

                status = st.selectbox(
                    "\u0421\u0442\u0430\u0442\u0443\u0441",
                    STATUS_OPTIONS,
                    index=0,
                )

                evidence_note = st.text_input(
                    "\u0417\u0430\u043c\u0435\u0442\u043a\u0430 "
                    "\u043e \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u0438",
                    value="",
                    placeholder="[\u0423\u0422\u041e\u0427\u041d\u0418\u0422\u042c]",
                )

                confirmed_by = st.text_input(
                    "\u041a\u0435\u043c \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u043e",
                    value="",
                )

                comment = st.text_input(
                    "\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439",
                    value="",
                )

                valid_from = st.text_input(
                    "\u0414\u0435\u0439\u0441\u0442\u0432\u0443\u0435\u0442 "
                    "\u0441 (YYYY-MM-DD)",
                    value="",
                )

                valid_until = st.text_input(
                    "\u0414\u0435\u0439\u0441\u0442\u0432\u0443\u0435\u0442 "
                    "\u043f\u043e (YYYY-MM-DD)",
                    value="",
                )

                if st.button(
                    "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c "
                    "\u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435"
                ):
                    try:
                        upsert_assignment(
                            conn,
                            company_id=company_id,
                            role_id=role_ids[role_index],
                            employee_id=employee_ids[employee_index],
                            status=status,
                            evidence_note=evidence_note.strip() or None,
                            confirmed_by=confirmed_by.strip() or None,
                            comment=comment.strip() or None,
                            valid_from=valid_from.strip() or None,
                            valid_until=valid_until.strip() or None,
                        )
                        conn.commit()
                        st.success(
                            "\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e."
                        )
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    finally:
        conn.close()


render = render_responsibilities
