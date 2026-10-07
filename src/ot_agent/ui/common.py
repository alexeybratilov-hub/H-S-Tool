from __future__ import annotations

import streamlit as st

from ot_agent.db import list_companies


def render_company_selector(
    label: str = "\u0422\u0435\u043a\u0443\u0449\u0430\u044f \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u044f",
    key: str = "global_company_selector",
) -> str | None:
    companies = list_companies()

    if not companies:
        st.warning(
            "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 "
            "\u0441\u043e\u0437\u0434\u0430\u0439\u0442\u0435 "
            "\u0445\u043e\u0442\u044f \u0431\u044b "
            "\u043e\u0434\u043d\u0443 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u044e "
            "\u0432 \u0440\u0430\u0437\u0434\u0435\u043b\u0435 Companies."
        )
        return None

    options = [str(company["company_id"]) for company in companies]

    labels = {
        str(company["company_id"]): (
            f"{company.get('legal_name') or company['company_id']} "
            f"({company['company_id']})"
        )
        for company in companies
    }

    current = st.session_state.get("current_company_id")

    if current not in options:
        current = options[0]

    selected = st.selectbox(
        label,
        options,
        index=options.index(current),
        format_func=lambda company_id: labels.get(company_id, company_id),
        key=key,
    )

    st.session_state.current_company_id = selected
    return selected