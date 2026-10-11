import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
from ot_agent.ui.sout_ppe_risk import render as render_sout_ppe_risk
from ot_agent.periodic_control_db import init_periodic_schema
from ot_agent.drafts_db import init_draft_schema
from ot_agent.package_planner_db import init_package_schema
from ot_agent.position_profiles_db import init_position_profiles_schema
from ot_agent.responsibility_db import init_responsibility_schema

from ot_agent.applicability_db import init_applicability_schema
from ot_agent.db import init_db
from ot_agent.regulatory_db import init_regulatory_schema
from ot_agent.baseline_db import get_connection, init_baseline_schema
from ot_agent.security import get_security_notice
from ot_agent.ui import (
    periodic_control,
    drafts,
    package_planner,
    position_profiles,
    responsibilities,
    baseline_catalog,
    companies,
    dashboard,
    normative_base,
    norm_applicability,
    registers,
    settings,
    staffing,
    document_upload,
)

init_db()
init_regulatory_schema()
init_applicability_schema()
init_responsibility_schema()
init_position_profiles_schema()
init_package_schema()
init_draft_schema()
init_periodic_schema()

st.set_page_config(
    page_title="OT Local Agent",
    page_icon="\U0001F6E1",
    layout="wide",
)

st.title("OT Local Agent \u2014 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u044b\u0439 MVP")
st.caption(get_security_notice())

page = st.sidebar.radio(
    "\u0420\u0430\u0437\u0434\u0435\u043b\u044b",
    [
        "\u041f\u0430\u043d\u0435\u043b\u044c \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f",
        "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u0438",
        "\u0420\u0435\u0435\u0441\u0442\u0440\u044b",
        "\u0428\u0442\u0430\u0442\u043d\u043e\u0435 \u0440\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
        "\u041d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u0430\u044f \u0431\u0430\u0437\u0430",
        "\u041f\u0440\u0438\u043c\u0435\u043d\u0438\u043c\u043e\u0441\u0442\u044c \u043d\u043e\u0440\u043c",
        "\u0411\u0430\u0437\u043e\u0432\u044b\u0439 \u043a\u0430\u0442\u0430\u043b\u043e\u0433",
        "\u0427\u0435\u043a\u043b\u0438\u0441\u0442 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0445",
        "\u041f\u0440\u043e\u0444\u0438\u043b\u0438 \u0434\u043e\u043b\u0436\u043d\u043e\u0441\u0442\u0435\u0439",
        "\u041f\u0430\u043a\u0435\u0442\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432",
        "\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432",
        "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a\u0438",
        "\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c \u0441\u0440\u043e\u043a\u043e\u0432",
        "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438",
    ],
)

if page == "\u041f\u0430\u043d\u0435\u043b\u044c \u0443\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f":
    dashboard.render()
elif page == "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u0438":
    companies.render()
elif page == "\u0420\u0435\u0435\u0441\u0442\u0440\u044b":
    registers.render()
elif page == "\u0428\u0442\u0430\u0442\u043d\u043e\u0435 \u0440\u0430\u0441\u043f\u0438\u0441\u0430\u043d\u0438\u0435":
    staffing.render()
elif page == "\u041d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u0430\u044f \u0431\u0430\u0437\u0430":
    normative_base.render()
elif page == "\u041f\u0440\u0438\u043c\u0435\u043d\u0438\u043c\u043e\u0441\u0442\u044c \u043d\u043e\u0440\u043c":
    norm_applicability.render()
elif page == "\u0411\u0430\u0437\u043e\u0432\u044b\u0439 \u043a\u0430\u0442\u0430\u043b\u043e\u0433":
    baseline_catalog.render()
elif page == "\u0427\u0435\u043a\u043b\u0438\u0441\u0442 \u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0445":
    responsibilities.render()
elif page == "\u041f\u0440\u043e\u0446\u0435\u0434\u0443\u0440\u044b \u0430\u0442\u0442\u0435\u0441\u0442\u0430\u0446\u0438\u0438":
    position_profiles.render()
elif page == "\u041f\u0430\u043a\u0435\u0442\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432":
    package_planner.render()
elif page == "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a\u0438":
    drafts.render()
elif page == "\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c \u0441\u0440\u043e\u043a\u043e\u0432":
    periodic_control.render()
elif page == "\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432":
    document_upload.render()
else:
    settings.render()
