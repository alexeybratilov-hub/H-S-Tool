import pandas as pd
import streamlit as st

from ot_agent.ppe_sout_risk_db import DB_PATH, get_connection

SOURCE_TYPE = "STAGE13_PRELIMINARY"

HEADER = "\u041f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f \u042d\u0442\u0430\u043f\u0430 13"
NOTE = "\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u044f. \u041d\u0435 \u044f\u0432\u043b\u044f\u044e\u0442\u0441\u044f \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d\u043d\u044b\u043c \u043f\u0435\u0440\u0435\u0447\u043d\u0435\u043c."
COMPANY = "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f"
STATUS = "\u0421\u0442\u0430\u0442\u0443\u0441"
ALL = "\u0412\u0441\u0435"
SEARCH = "\u041f\u043e\u0438\u0441\u043a"
NO_COMPANIES = "\u041d\u0435\u0442 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0439"
NO_ROWS = "\u041d\u0435\u0442 \u043f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0445 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u0439"
QUERY_ERROR = "\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u043f\u0440\u043e\u0441\u0430"


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


def render_stage13_requirements():
    st.header(HEADER)
    st.caption(NOTE)

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
        key="s13_req_company",
    )

    try:
        df = _df(
            """
            SELECT *
            FROM document_requirements
            WHERE company_id = ?
              AND source_type = ?
            ORDER BY code, title
            """,
            (company_id, SOURCE_TYPE),
        )
    except Exception as exc:
        st.error(f"{QUERY_ERROR}: {exc}")
        return

    if df.empty:
        st.info(NO_ROWS)
        return

    col1, col2 = st.columns(2)

    search = col1.text_input(SEARCH, key="s13_req_search")

    status_values = [ALL]
    if "status" in df.columns:
        status_values += sorted({str(v) for v in df["status"].dropna().tolist() if str(v)})

    selected_status = col2.selectbox(
        STATUS,
        status_values,
        key="s13_req_status",
    )

    out = df

    if search:
        mask = pd.Series(False, index=out.index)
        for c in out.columns:
            if out[c].dtype == object:
                mask |= out[c].astype(str).str.contains(search, case=False, na=False)
        out = out[mask]

    if "status" in out.columns and selected_status != ALL:
        out = out[out["status"].astype(str) == selected_status]

    if out.empty:
        st.info(NO_ROWS)
    else:
        st.dataframe(out)
