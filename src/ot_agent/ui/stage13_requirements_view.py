import pandas as pd
import streamlit as st

from ot_agent.ppe_sout_risk_db import DB_PATH, get_connection

SOURCE_TYPE = "STAGE13_PRELIMINARY"
ALLOWED_STATUSES = ("CONFIRMED", "REJECTED", "REQUIRES_VERIFICATION")

HEADER = "\u041f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f \u042d\u0442\u0430\u043f\u0430 13"
NOTE = "\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u044f. \u041d\u0435 \u044f\u0432\u043b\u044f\u044e\u0442\u0441\u044f \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d\u043d\u044b\u043c \u043f\u0435\u0440\u0435\u0447\u043d\u0435\u043c."
ACTION_NOTE = "\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u0435/\u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u0438\u0435 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u043c. \u041d\u0435 \u044f\u0432\u043b\u044f\u0435\u0442\u0441\u044f \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u0438\u043c \u0437\u0430\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435\u043c."
COMPANY = "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f"
STATUS = "\u0421\u0442\u0430\u0442\u0443\u0441"
ALL = "\u0412\u0441\u0435"
SEARCH = "\u041f\u043e\u0438\u0441\u043a"
TOTAL = "\u0412\u0441\u0435\u0433\u043e"
REQUIREMENT = "\u0417\u0430\u043f\u0438\u0441\u044c"
ACTIONS = "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u044f"
CONFIRM = "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438"
REJECT = "\u041e\u0442\u043a\u043b\u043e\u043d\u0438\u0442\u044c \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438"
RESET = "\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0432 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0443"
SAVED = "\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e"
SAVE_ERROR = "\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f"
NO_COMPANIES = "\u041d\u0435\u0442 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0439"
NO_ROWS = "\u041d\u0435\u0442 \u043f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0445 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u0439"
QUERY_ERROR = "\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u043f\u0440\u043e\u0441\u0430"


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


def _update_status(requirement_id: str, company_id: str, new_status: str) -> None:
    if new_status not in ALLOWED_STATUSES:
        raise ValueError("unsupported status")

    conn = get_connection(DB_PATH)

    try:
        cur = conn.cursor()

        row = cur.execute(
            """
            SELECT company_id, source_type, status
            FROM document_requirements
            WHERE requirement_id = ?
            """,
            (requirement_id,),
        ).fetchone()

        if row is None:
            raise ValueError("record not found")

        if row["company_id"] != company_id:
            raise ValueError("company mismatch")

        if row["source_type"] != SOURCE_TYPE:
            raise ValueError("not stage13 preliminary record")

        company = cur.execute(
            "SELECT 1 FROM companies WHERE company_id = ?",
            (company_id,),
        ).fetchone()

        if company is None:
            raise ValueError("company not found")

        cur.execute(
            """
            UPDATE document_requirements
            SET status = ?, updated_at = datetime('now')
            WHERE requirement_id = ?
              AND company_id = ?
              AND source_type = ?
            """,
            (new_status, requirement_id, company_id, SOURCE_TYPE),
        )

        if cur.rowcount != 1:
            conn.rollback()
            raise ValueError("update affected unexpected rows")

        conn.commit()

    except Exception:
        conn.rollback()
        raise

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
        key=f"s13_req_company_{_safe_key(company_id)}",
    )

    try:
        rows = _df(
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

    if rows.empty:
        st.info(NO_ROWS)
        return

    if "status" in rows.columns:
        counts = rows["status"].astype(str).value_counts().to_dict()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(TOTAL, len(rows))
        c2.metric("REQUIRES_VERIFICATION", counts.get("REQUIRES_VERIFICATION", 0))
        c3.metric("CONFIRMED", counts.get("CONFIRMED", 0))
        c4.metric("REJECTED", counts.get("REJECTED", 0))

    view = rows

    col1, col2 = st.columns(2)

    search = col1.text_input(
        SEARCH,
        key=f"s13_req_search_{_safe_key(company_id)}",
    )

    status_values = [ALL]

    if "status" in rows.columns:
        status_values += sorted(
            {str(v) for v in rows["status"].dropna().tolist() if str(v)}
        )

    selected_status = col2.selectbox(
        STATUS,
        status_values,
        key=f"s13_req_status_{_safe_key(company_id)}",
    )

    if search:
        mask = pd.Series(False, index=view.index)

        for c in view.columns:
            if view[c].dtype == object:
                mask |= view[c].astype(str).str.contains(search, case=False, na=False)

        view = view[mask]

    if "status" in view.columns and selected_status != ALL:
        view = view[view["status"].astype(str) == selected_status]

    st.dataframe(view)

    st.markdown(f"**{ACTIONS}**")
    st.caption(ACTION_NOTE)

    if "requirement_id" not in rows.columns:
        st.info(NO_ROWS)
        return

    ids = []
    labels = []

    for _, row in rows.iterrows():
        rid = str(row.get("requirement_id", "")).strip()

        if not rid:
            continue

        code = str(row.get("code", ""))
        title = str(row.get("title", ""))
        status = str(row.get("status", ""))

        ids.append(rid)
        labels.append(f"{code} | {title} | {status}")

    if not ids:
        st.info(NO_ROWS)
        return

    idx = st.selectbox(
        REQUIREMENT,
        range(len(ids)),
        format_func=lambda i: labels[i],
        key=f"s13_req_action_{_safe_key(company_id)}",
    )

    rid = ids[idx]
    safe_rid = _safe_key(rid)

    b1, b2, b3 = st.columns(3)

    if b1.button(CONFIRM, key=f"s13_confirm_{safe_rid}"):
        try:
            _update_status(rid, company_id, "CONFIRMED")
            st.success(SAVED)
            st.rerun()
        except Exception as exc:
            st.error(f"{SAVE_ERROR}: {exc}")

    if b2.button(REJECT, key=f"s13_reject_{safe_rid}"):
        try:
            _update_status(rid, company_id, "REJECTED")
            st.success(SAVED)
            st.rerun()
        except Exception as exc:
            st.error(f"{SAVE_ERROR}: {exc}")

    if b3.button(RESET, key=f"s13_reset_{safe_rid}"):
        try:
            _update_status(rid, company_id, "REQUIRES_VERIFICATION")
            st.success(SAVED)
            st.rerun()
        except Exception as exc:
            st.error(f"{SAVE_ERROR}: {exc}")
