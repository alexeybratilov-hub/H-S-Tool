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
        "Synthetic technical checklist. "
        "Not a legal register. "
        "Role codes are technical identifiers and require verification."
    )

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
        )

        company_id = company_ids[company_index]

        counts = count_assignments_by_status(conn, company_id)

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Total", counts["total"])
        c2.metric("PROPOSED", counts["PROPOSED"])
        c3.metric("CONFIRMED", counts["CONFIRMED"])
        c4.metric("MISSING_EVIDENCE", counts["MISSING_EVIDENCE"])
        c5.metric("REQUIRES_VERIFICATION", counts["REQUIRES_VERIFICATION"])
        c6.metric("REJECTED", counts["REJECTED"])

        assignments = list_assignments(conn, company_id)

        if assignments:
            st.dataframe(assignments, hide_index=True, width="stretch")
        else:
            st.info("No assignments for this company.")

        with st.expander("Add or update assignment"):
            roles = list_roles(conn)
            employees = list_employees(conn, company_id)

            if not roles:
                st.info("No roles found.")
            elif not employees:
                st.info("No employees found for the selected company.")
            else:
                role_labels = [
                    f"{role['code']} | {role['title']}"
                    for role in roles
                ]
                role_ids = [role["role_id"] for role in roles]

                employee_labels = [
                    f"{employee['employee_id']} | {employee['display_name']}"
                    for employee in employees
                ]
                employee_ids = [
                    employee["employee_id"]
                    for employee in employees
                ]

                role_index = st.selectbox(
                    "Role",
                    range(len(role_labels)),
                    format_func=lambda i: role_labels[i],
                )

                employee_index = st.selectbox(
                    "Employee",
                    range(len(employee_labels)),
                    format_func=lambda i: employee_labels[i],
                )

                status = st.selectbox(
                    "Status",
                    STATUS_OPTIONS,
                    index=0,
                )

                evidence_note = st.text_input(
                    "Evidence note",
                    value="",
                    placeholder="[TBD]",
                )

                confirmed_by = st.text_input(
                    "Confirmed by",
                    value="",
                )

                comment = st.text_input(
                    "Comment",
                    value="",
                )

                valid_from = st.text_input(
                    "Valid from (YYYY-MM-DD)",
                    value="",
                )

                valid_until = st.text_input(
                    "Valid until (YYYY-MM-DD)",
                    value="",
                )

                if st.button("Save assignment"):
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
                        st.success("Saved.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    finally:
        conn.close()


render = render_responsibilities
