import streamlit as st
from pathlib import Path
from ot_agent.baseline_db import get_connection, count_baseline_by_status, list_baseline_documents, update_baseline_status

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"
STATUS_OPTIONS = ["SUGGESTED", "USER_CONFIRMED", "USER_REJECTED", "REQUIRES_VERIFICATION"]

def render_baseline_catalog():
    st.title("\u0411\u0430\u0437\u043e\u0432\u044b\u0439 \u043a\u0430\u0442\u0430\u043b\u043e\u0433 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432")
    st.warning("DRAFT / REQUIRES_VERIFICATION. \u0422\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u0435 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0441\u0442\u043e\u043c.")
    
    conn = get_connection(DB_PATH)
    try:
        counts = count_baseline_by_status(conn, topic="OT")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("\u0412\u0441\u0435\u0433\u043e", counts["total"])
        c2.metric("SUGGESTED", counts["SUGGESTED"])
        c3.metric("CONFIRMED", counts["USER_CONFIRMED"])
        c4.metric("REJECTED", counts["USER_REJECTED"])
        c5.metric("VERIFY", counts["REQUIRES_VERIFICATION"])

        search = st.text_input("\u041f\u043e\u0438\u0441\u043a")
        status_filter = st.selectbox("\u0421\u0442\u0430\u0442\u0443\u0441", ["ALL"] + STATUS_OPTIONS)
        
        docs = list_baseline_documents(conn, topic="OT", status=None if status_filter == "ALL" else status_filter, search=search)
        st.dataframe(docs, hide_index=True, width="stretch")
    finally:
        conn.close()

render = render_baseline_catalog
