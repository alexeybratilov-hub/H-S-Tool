import pandas as pd
import streamlit as st

from ot_agent.ppe_sout_risk_db import DB_PATH, get_connection

TITLE = "\u0421\u041e\u0423\u0422 / \u0421\u0418\u0417 / \u0420\u0438\u0441\u043a\u0438"
NOTE = "\u0421\u0438\u043d\u0442\u0435\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u0434\u0430\u043d\u043d\u044b\u0435. \u0422\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f \u0432\u0435\u0440\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f."
COMPANY = "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f"
SECTION = "\u0420\u0430\u0437\u0434\u0435\u043b"
OVERVIEW = "\u041e\u0431\u0437\u043e\u0440"
SOUT = "\u0421\u041e\u0423\u0422"
PPE = "\u0421\u0418\u0417"
RISK = "\u0420\u0438\u0441\u043a\u0438"
NO_COMPANIES = "\u041d\u0435\u0442 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0439"
NO_DATA = "\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445"

TABLES = (
    "harmful_factors",
    "sout_campaigns",
    "sout_workplaces",
    "sout_results",
    "ppe_items",
    "ppe_norms",
    "employee_ppe_cards",
    "ppe_issue_records",
    "ppe_return_records",
    "risk_register",
)


def _df(sql, params=()):
    conn = get_connection(DB_PATH)
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
        st.dataframe(df)


def render():
    st.header(TITLE)
    st.caption(NOTE)

    companies = _df("SELECT company_id FROM companies ORDER BY company_id")
    if companies.empty:
        st.info(NO_COMPANIES)
        return

    company_id = st.selectbox(
        COMPANY,
        companies["company_id"].tolist(),
        key="sout_ppe_risk_company",
    )

    section = st.selectbox(
        SECTION,
        [OVERVIEW, SOUT, PPE, RISK],
        key="sout_ppe_risk_section",
    )

    if section == OVERVIEW:
        rows = []
        for table in TABLES:
            rows.append({"table": table, "rows": len(_df(f"SELECT * FROM {table}"))})
        st.dataframe(pd.DataFrame(rows))

    elif section == SOUT:
        _show(
            "sout_campaigns",
            _df("SELECT * FROM sout_campaigns WHERE company_id=?", (company_id,)),
        )
        _show(
            "sout_workplaces",
            _df("SELECT * FROM sout_workplaces WHERE company_id=?", (company_id,)),
        )
        _show(
            "sout_results",
            _df(
                """
                SELECT sr.*
                FROM sout_results sr
                JOIN sout_workplaces sw ON sr.workplace_id = sw.workplace_id
                WHERE sw.company_id = ?
                ORDER BY sr.rowid
                """,
                (company_id,),
            ),
        )

    elif section == PPE:
        _show("ppe_items", _df("SELECT * FROM ppe_items"))
        _show(
            "ppe_norms",
            _df("SELECT * FROM ppe_norms WHERE company_id=?", (company_id,)),
        )
        _show(
            "employee_ppe_cards",
            _df("SELECT * FROM employee_ppe_cards WHERE company_id=?", (company_id,)),
        )
        _show(
            "ppe_issue_records",
            _df("SELECT * FROM ppe_issue_records WHERE company_id=?", (company_id,)),
        )
        _show(
            "ppe_return_records",
            _df("SELECT * FROM ppe_return_records WHERE company_id=?", (company_id,)),
        )

    elif section == RISK:
        _show(
            "risk_register",
            _df("SELECT * FROM risk_register WHERE company_id=?", (company_id,)),
        )
