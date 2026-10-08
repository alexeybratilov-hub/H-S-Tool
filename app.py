import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
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
)

init_db()
init_regulatory_schema()
init_applicability_schema()
init_responsibility_schema()
init_position_profiles_schema()
init_package_schema()
init_draft_schema()

st.set_page_config(
    page_title="OT Local Agent",
    page_icon="\U0001F6E1",
    layout="wide",
)

st.title("OT Local Agent \u2014 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u044b\u0439 MVP")
st.caption(get_security_notice())

page = st.sidebar.radio(
    "Разделы",
    [
        "Панель управления",
        "Компании",
        "Реестры",
        "Штатное расписание",
        "Нормативная база",
        "Применимость норм",
        "Базовый каталог",
        "Чеклист ответственных",
        "Профили должностей",
        "Пакетдокументов",
        "Черновики",
        "Настройки",
    ],
)

if page == "Панель управления":
    dashboard.render()
elif page == "Компании":
    companies.render()
elif page == "Реестры":
    registers.render()
elif page == "Штатное расписание":
    staffing.render()
elif page == "Нормативная база":
    normative_base.render()
elif page == "Применимость норм":
    norm_applicability.render()
elif page == "Базовый каталог":
    baseline_catalog.render()
elif page == "Чеклист ответственных":
    responsibilities.render()
elif page == "Профили должностей":
    position_profiles.render()
elif page == "Пакетдокументов":
    package_planner.render()
elif page == "Черновики":
    drafts.render()
else:
    settings.render()