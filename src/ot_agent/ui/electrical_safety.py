import pandas as pd
import streamlit as st

from ot_agent.electrical_safety_db import EXPECTED_TABLES, get_connection

TITLE = "\u042d\u043b\u0435\u043a\u0442\u0440\u043e\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u044c"
NOTE = "\u0421\u0438\u043d\u0442\u0435\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u0434\u0430\u043d\u043d\u044b\u0435. \u0422\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f \u0432\u0435\u0440\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f."
WARNING = "\u0422\u043e\u043b\u044c\u043a\u043e \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440. \u0411\u0435\u0437 \u0440\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f, \u0431\u0435\u0437 LLM, \u0431\u0435\u0437 DOCX, \u0431\u0435\u0437 \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u043e\u0433\u043e \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f."
COMPANY = "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f"
SECTION = "\u0420\u0430\u0437\u0434\u0435\u043b"
OVERVIEW = "\u041e\u0431\u0437\u043e\u0440"
GROUP_CATALOG = "\u041a\u0430\u0442\u0430\u043b\u043e\u0433 \u0433\u0440\u0443\u043f\u043f"
INSTALLATIONS = "\u042d\u043b\u0435\u043a\u0442\u0440\u043e\u0443\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0438"
COMMISSIONS = "\u041a\u043e\u043c\u0438\u0441\u0441\u0438\u0438"
MEMBERS = "\u0421\u043e\u0441\u0442\u0430\u0432 \u043a\u043e\u043c\u0438\u0441\u0441\u0438\u0439"
PROTOCOLS = "\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u044b \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438 \u0437\u043d\u0430\u043d\u0438\u0439"
PROTOCOL_ITEMS = "\u041f\u043e\u0437\u0438\u0446\u0438\u0438 \u043f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u043e\u0432"
QUALIFICATIONS = "\u041a\u0432\u0430\u043b\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u0438 \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u043e\u0432"
PERMITS = "\u0414\u043e\u043f\u0443\u0441\u043a\u0438"
NO_COMPANIES = "\u041d\u0435\u0442 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0439"
NO_DATA = "\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445"
QUERY_ERROR = "\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u043f\u0440\u043e\u0441\u0430"

SECTIONS = (
    OVERVIEW,
    GROUP_CATALOG,
    INSTALLATIONS,
    COMMISSIONS,
    MEMBERS,
    PROTOCOLS,
    PROTOCOL_ITEMS,
    QUALIFICATIONS,
    PERMITS,
)


def _df(sql, params=()):
    conn = get_connection()

    try:
        if params:
            cur = conn.execute(sql, params)
        else:
            cur = conn.execute(sql)

        cols = [d[0] for d in cur.description]
        rows = [tuple(r) for r in cur.fetchall()]
        return pd.DataFrame(rows, columns=cols)

    finally:
        conn.close()


def _show(title, df):
    st.markdown(f"**{title}**")

    if df.empty:
        st.info(NO_DATA)
    else:
        st.dataframe(df, hide_index=True)


def _safe_show(title, sql, params=()):
    try:
        df = _df(sql, params)
        _show(title, df)
    except Exception as exc:
        st.error(f"{QUERY_ERROR}: {exc}")


def _overview():
    rows = []

    for table in EXPECTED_TABLES:
        try:
            df = _df(f"SELECT COUNT(*) AS rows FROM {table}")
            rows.append({"table": table, "rows": int(df.iloc[0, 0])})
        except Exception:
            rows.append({"table": table, "rows": "MISSING"})

    st.dataframe(pd.DataFrame(rows), hide_index=True)


def _render_section(company_id, section):
    if section == OVERVIEW:
        _overview()

    elif section == GROUP_CATALOG:
        _safe_show(
            GROUP_CATALOG,
            """
            SELECT *
            FROM electrical_group_catalog
            ORDER BY group_code
            """,
        )

    elif section == INSTALLATIONS:
        _safe_show(
            INSTALLATIONS,
            """
            SELECT *
            FROM electrical_installations
            WHERE company_id = ?
            ORDER BY installation_id
            """,
            (company_id,),
        )

    elif section == COMMISSIONS:
        _safe_show(
            COMMISSIONS,
            """
            SELECT *
            FROM electrical_commissions
            WHERE company_id = ?
            ORDER BY commission_id
            """,
            (company_id,),
        )

    elif section == MEMBERS:
        _safe_show(
            MEMBERS,
            """
            SELECT
                cm.*,
                ec.name AS commission_name
            FROM commission_members cm
            JOIN electrical_commissions ec
              ON ec.commission_id = cm.commission_id
            WHERE cm.company_id = ?
            ORDER BY cm.commission_id, cm.role_code, cm.employee_id
            """,
            (company_id,),
        )

    elif section == PROTOCOLS:
        _safe_show(
            PROTOCOLS,
            """
            SELECT
                kp.*,
                ec.name AS commission_name
            FROM knowledge_check_protocols kp
            LEFT JOIN electrical_commissions ec
              ON ec.commission_id = kp.commission_id
            WHERE kp.company_id = ?
            ORDER BY kp.check_date, kp.protocol_id
            """,
            (company_id,),
        )

    elif section == PROTOCOL_ITEMS:
        _safe_show(
            PROTOCOL_ITEMS,
            """
            SELECT
                pi.*,
                kp.protocol_number
            FROM protocol_items pi
            JOIN knowledge_check_protocols kp
              ON kp.protocol_id = pi.protocol_id
            WHERE pi.company_id = ?
            ORDER BY pi.protocol_id, pi.employee_id, pi.group_code
            """,
            (company_id,),
        )

    elif section == QUALIFICATIONS:
        _safe_show(
            QUALIFICATIONS,
            """
            SELECT
                q.*,
                kp.protocol_number
            FROM employee_electrical_qualifications q
            LEFT JOIN knowledge_check_protocols kp
              ON kp.protocol_id = q.protocol_id
            WHERE q.company_id = ?
            ORDER BY q.employee_id, q.group_code, q.valid_from
            """,
            (company_id,),
        )

    elif section == PERMITS:
        _safe_show(
            PERMITS,
            """
            SELECT
                p.*,
                ei.name AS installation_name
            FROM electrical_permits p
            LEFT JOIN electrical_installations ei
              ON ei.installation_id = p.installation_id
            WHERE p.company_id = ?
            ORDER BY p.employee_id, p.permit_type_code
            """,
            (company_id,),
        )

    else:
        st.info(NO_DATA)


def render():
    st.header(TITLE)
    st.caption(NOTE)
    st.caption(WARNING)

    try:
        companies = _df("SELECT company_id FROM companies ORDER BY company_id")
    except Exception as exc:
        st.error(f"{QUERY_ERROR}: {exc}")
        return

    if companies.empty:
        st.info(NO_COMPANIES)
        return

    company_id = st.selectbox(
        COMPANY,
        companies["company_id"].tolist(),
        key="electrical_company",
    )

    section = st.selectbox(
        SECTION,
        SECTIONS,
        key="electrical_section",
    )

    _render_section(company_id, section)
