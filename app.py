import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st

from ot_agent.db import init_db
from ot_agent.security import get_security_notice
from ot_agent.ui import companies, dashboard, registers, settings

init_db()

st.set_page_config(
    page_title="OT Local Agent",
    page_icon="🛡️",
    layout="wide",
)

st.title("OT Local Agent — локальный MVP")
st.caption(get_security_notice())

page = st.sidebar.radio(
    "Разделы",
    [
        "Dashboard",
        "Companies",
        "Registers",
        "Settings",
    ],
)

if page == "Dashboard":
    dashboard.render()
elif page == "Companies":
    companies.render()
elif page == "Registers":
    registers.render()
else:
    settings.render()