import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st

from ot_agent.applicability_db import init_applicability_schema
from ot_agent.db import init_db
from ot_agent.regulatory_db import init_regulatory_schema
from ot_agent.security import get_security_notice
from ot_agent.ui import (
    companies,
    dashboard,
    normative_base,
    norm_applicability,
    registers,
    settings,
    staffing,
)

init_db()
init_regulatory_schema()
init_applicability_schema()

st.set_page_config(
    page_title="OT Local Agent",
    page_icon="\U0001F6E1",
    layout="wide",
)

st.title("OT Local Agent \u2014 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u044b\u0439 MVP")
st.caption(get_security_notice())

page = st.sidebar.radio(
    "Sections",
    [
        "Dashboard",
        "Companies",
        "Registers",
        "Staffing",
        "Normative Base",
        "Norm Applicability",
        "Settings",
    ],
)

if page == "Dashboard":
    dashboard.render()
elif page == "Companies":
    companies.render()
elif page == "Registers":
    registers.render()
elif page == "Staffing":
    staffing.render()
elif page == "Normative Base":
    normative_base.render()
elif page == "Norm Applicability":
    norm_applicability.render()
else:
    settings.render()