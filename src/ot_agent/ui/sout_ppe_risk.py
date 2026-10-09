import pandas as pd
import streamlit as st

from ot_agent.ppe_sout_risk_db import DB_PATH, get_connection
from ot_agent import stage13_forms_db as forms_db

TITLE = "\u0421\u041e\u0423\u0422 / \u0421\u0418\u0417 / \u0420\u0438\u0441\u043a\u0438"
NOTE = "\u0421\u0438\u043d\u0442\u0435\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u0434\u0430\u043d\u043d\u044b\u0435. \u0422\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f \u0432\u0435\u0440\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f."
WARNING_EDIT = "\u0422\u043e\u043b\u044c\u043a\u043e \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u043f\u043e\u043b\u044f. \u0411\u0435\u0437 \u0434\u0438\u0430\u0433\u043d\u043e\u0437\u043e\u0432."
COMPANY = "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f"
MODE = "\u0420\u0435\u0436\u0438\u043c"
VIEW = "\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440"
EDIT = "\u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 metadata"
SECTION = "\u0420\u0430\u0437\u0434\u0435\u043b"
OVERVIEW = "\u041e\u0431\u0437\u043e\u0440"
SOUT = "\u0421\u041e\u0423\u0422"
PPE = "\u0421\u0418\u0417"
RISK = "\u0420\u0438\u0441\u043a\u0438"
TABLE_LABEL = "\u0422\u0430\u0431\u043b\u0438\u0446\u0430"
RECORD_LABEL = "\u0417\u0430\u043f\u0438\u0441\u044c"
SAVE_BUTTON = "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c"
SAVED = "\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e"
NO_CHANGES = "\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0439 \u043d\u0435\u0442"
SAVE_ERROR = "\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f"
NO_COMPANIES = "\u041d\u0435\u0442 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0439"
NO_DATA = "\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445"
NO_RECORDS = "\u041d\u0435\u0442 \u0437\u0430\u043f\u0438\u0441\u0435\u0439"
RECORD_MISSING = "\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430"

TABLES_OVERVIEW = (
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

EDITABLE_TABLES = tuple(forms_db.TABLE_CONFIG.keys())


def _safe_key(value: object) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in str(value))


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


def _render_view(company_id):
    section = st.selectbox(
        SECTION,
        [OVERVIEW, SOUT, PPE, RISK],
        key="sout_ppe_risk_section",
    )

    if section == OVERVIEW:
        rows = []
        for table in TABLES_OVERVIEW:
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


def _render_edit(company_id):
    table = st.selectbox(
        TABLE_LABEL,
        EDITABLE_TABLES,
        key="s13_edit_table",
    )

    cfg = forms_db.TABLE_CONFIG[table]

    conn = forms_db.get_connection(DB_PATH)
    try:
        records = forms_db.list_records(conn, table, company_id)
    finally:
        conn.close()

    if not records:
        st.info(NO_RECORDS)
        return

    labels = []
    for rec in records:
        parts = []
        for col in cfg["display_cols"][:3]:
            value = rec.get(col)
            parts.append("" if value is None else str(value))
        labels.append(" | ".join(parts))

    idx = st.selectbox(
        RECORD_LABEL,
        range(len(records)),
        format_func=lambda i: labels[i],
        key=f"s13_edit_record_{table}",
    )

    rec = records[idx]
    pk = rec[cfg["pk"]]
    safe_pk = _safe_key(pk)

    conn = forms_db.get_connection(DB_PATH)
    try:
        full = forms_db.get_record(conn, table, pk, company_id)
    finally:
        conn.close()

    if full is None:
        st.error(RECORD_MISSING)
        return

    st.markdown(f"**{TABLE_LABEL}: {table}**")
    st.caption(f"{cfg['pk']}: {pk}")
    st.caption(WARNING_EDIT)

    cols = st.columns(2)
    values = {}

    for i, field in enumerate(cfg["editable"]):
        current = full.get(field)
        current_str = "" if current is None else str(current)

        with cols[i % 2]:
            values[field] = st.text_input(
                field,
                value=current_str,
                key=f"s13_{table}_{safe_pk}_{field}",
            )

    if st.button(SAVE_BUTTON, key=f"s13_save_{table}_{safe_pk}"):
        required = set(cfg.get("required", ()))
        pending = {}

        for field, val in values.items():
            old = full.get(field)
            old_str = "" if old is None else str(old)
            new_str = str(val).strip()

            if new_str == old_str:
                continue

            if new_str == "" and field in required:
                continue

            pending[field] = val

        if not pending:
            st.info(NO_CHANGES)
        else:
            conn = forms_db.get_connection(DB_PATH)
            try:
                updated = forms_db.update_record(
                    conn,
                    table,
                    pk,
                    company_id,
                    pending,
                )
                st.success(SAVED)
                st.json(updated)
            except Exception as exc:
                st.error(f"{SAVE_ERROR}: {exc}")
            finally:
                conn.close()


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

    mode = st.selectbox(
        MODE,
        [VIEW, EDIT],
        key="sout_ppe_risk_mode",
    )

    if mode == VIEW:
        _render_view(company_id)
    else:
        _render_edit(company_id)
