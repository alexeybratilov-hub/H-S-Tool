import streamlit as st
from pathlib import Path

from ot_agent.package_planner_db import (
    count_requirements_by_status,
    create_package,
    generate_requirements_for_company,
    get_connection,
    list_companies,
    list_package_items,
    list_packages,
    list_requirements,
    populate_package_draft,
    update_requirement,
)

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

STATUS_OPTIONS = [
    "SUGGESTED",
    "CONFIRMED",
    "REJECTED",
    "REQUIRES_VERIFICATION",
]

TITLE = "\u041f\u0430\u043a\u0435\u0442 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432"

WARNING = (
    "DRAFT / REQUIRES_VERIFICATION. "
    "\u0421\u0438\u043d\u0442\u0435\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0439 "
    "\u0447\u0435\u0440\u043d\u043e\u0432\u043e\u0439 "
    "\u043f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a. "
    "\u041d\u0435 \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u0438 "
    "\u043f\u043e\u043b\u043d\u044b\u0439 "
    "\u043f\u0435\u0440\u0435\u0447\u0435\u043d\u044c. "
    "\u0422\u0440\u0435\u0431\u0443\u0435\u0442 "
    "\u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438 "
    "\u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0441\u0442\u043e\u043c."
)

COMPANY = "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f"
TOTAL = "\u0412\u0441\u0435\u0433\u043e"
STATUS = "\u0421\u0442\u0430\u0442\u0443\u0441"
PRIORITY = "\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442"
DEPENDENCIES = "\u0417\u0430\u0432\u0438\u0441\u0438\u043c\u043e\u0441\u0442\u0438"
NOTE = "\u0417\u0430\u043c\u0435\u0442\u043a\u0430"
REQUIREMENT = "\u0422\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u0435"
PACKAGES = "\u041f\u0430\u043a\u0435\u0442\u044b"
PACKAGE_ITEMS = "\u041f\u043e\u0437\u0438\u0446\u0438\u0438 \u043f\u0430\u043a\u0435\u0442\u0430"
NO_DATA = "\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445"
NO_COMPANIES = "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u0438 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b"
NO_REQUIREMENTS = "\u0422\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b"
NO_PACKAGES = "\u041f\u0430\u043a\u0435\u0442\u044b \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b"
UPDATE_REQ = "\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f \u0438\u0437 \u043a\u0430\u0442\u0430\u043b\u043e\u0433\u0430"
BUILD_PACKAGE = "\u0421\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0447\u0435\u0440\u043d\u043e\u0432\u043e\u0439 \u043f\u0430\u043a\u0435\u0442"
SAVE = "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c"
SAVED = "\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e."
SEARCH = "\u041f\u043e\u0438\u0441\u043a"


def render_package_planner() -> None:
    st.title(TITLE)
    st.warning(WARNING)

    conn = get_connection(DB_PATH)

    try:
        companies = list_companies(conn)

        if not companies:
            st.info(NO_COMPANIES)
            return

        company_labels = [company["display_name"] for company in companies]
        company_ids = [company["company_id"] for company in companies]

        company_index = st.selectbox(
            COMPANY,
            range(len(company_labels)),
            format_func=lambda i: company_labels[i],
        )

        company_id = company_ids[company_index]

        if st.button(UPDATE_REQ):
            try:
                count = generate_requirements_for_company(conn, company_id)
                conn.commit()
                st.success(f"{SAVED} {count}")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        counts = count_requirements_by_status(conn, company_id)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(TOTAL, counts["total"])
        c2.metric("SUGGESTED", counts["SUGGESTED"])
        c3.metric("CONFIRMED", counts["CONFIRMED"])
        c4.metric("REJECTED", counts["REJECTED"])
        c5.metric("REQUIRES_VERIFICATION", counts["REQUIRES_VERIFICATION"])

        search = st.text_input(SEARCH, value="")
        status_filter = st.selectbox(
            STATUS,
            ["ALL"] + STATUS_OPTIONS,
            index=0,
        )

        requirements = list_requirements(
            conn,
            company_id,
            status=None if status_filter == "ALL" else status_filter,
            search=search.strip() if search else None,
        )

        if requirements:
            st.dataframe(requirements, hide_index=True, width="stretch")
        else:
            st.info(NO_REQUIREMENTS)

        with st.expander(REQUIREMENT):
            if not requirements:
                st.info(NO_REQUIREMENTS)
            else:
                labels = [
                    f"{requirement['code']} | {requirement['title']}"
                    for requirement in requirements
                ]
                ids = [
                    requirement["requirement_id"]
                    for requirement in requirements
                ]

                requirement_index = st.selectbox(
                    REQUIREMENT,
                    range(len(labels)),
                    format_func=lambda i: labels[i],
                )

                current = requirements[requirement_index]

                current_status = current.get("status") or "SUGGESTED"
                status_index = (
                    STATUS_OPTIONS.index(current_status)
                    if current_status in STATUS_OPTIONS
                    else 0
                )

                status = st.selectbox(
                    STATUS,
                    STATUS_OPTIONS,
                    index=status_index,
                )

                priority = st.number_input(
                    PRIORITY,
                    value=int(current.get("priority") or 100),
                    min_value=1,
                    max_value=9999,
                )

                dependency_note = st.text_input(
                    DEPENDENCIES,
                    value=current.get("dependency_note") or "",
                )

                user_note = st.text_area(
                    NOTE,
                    value=current.get("user_note") or "",
                )

                if st.button(SAVE):
                    try:
                        update_requirement(
                            conn,
                            requirement_id=ids[requirement_index],
                            company_id=company_id,
                            status=status,
                            priority=int(priority),
                            dependency_note=dependency_note.strip() or None,
                            user_note=user_note.strip() or None,
                        )
                        conn.commit()
                        st.success(SAVED)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

        st.subheader(PACKAGES)

        if st.button(BUILD_PACKAGE):
            try:
                package_id = create_package(
                    conn,
                    company_id=company_id,
                    name="OT draft package",
                    note="Synthetic draft package. Requires verification.",
                )
                items_count = populate_package_draft(conn, package_id)
                conn.commit()
                st.success(
                    f"{SAVED} package_id={package_id}, items={items_count}"
                )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        packages = list_packages(conn, company_id)

        if not packages:
            st.info(NO_PACKAGES)
            return

        package_labels = [
            f"{package['package_id']} | {package['name']} | items={package['item_count']}"
            for package in packages
        ]
        package_ids = [package["package_id"] for package in packages]

        package_index = st.selectbox(
            PACKAGES,
            range(len(package_labels)),
            format_func=lambda i: package_labels[i],
        )

        st.dataframe(packages, hide_index=True, width="stretch")

        st.subheader(PACKAGE_ITEMS)

        items = list_package_items(conn, package_ids[package_index])

        if items:
            st.dataframe(items, hide_index=True, width="stretch")
        else:
            st.info(NO_DATA)

    finally:
        conn.close()


render = render_package_planner


# STAGE13_REQUIREMENTS_UI_PATCH_BEGIN
_orig_render_stage13 = globals().get("render")

if callable(_orig_render_stage13):
    def render(*args, **kwargs):
        _orig_render_stage13(*args, **kwargs)

        try:
            from ot_agent.ui.stage13_requirements_view import render_stage13_requirements
            render_stage13_requirements()
        except Exception as exc:
            import streamlit as st
            st.error("\u041e\u0448\u0438\u0431\u043a\u0430 \u043e\u0442\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u0439 \u042d\u0442\u0430\u043f\u0430 13: " + str(exc))
# STAGE13_REQUIREMENTS_UI_PATCH_END
