from __future__ import annotations

import streamlit as st

from ot_agent.db import list_companies


def render_company_selector(
    label: str = "Текущая компания",
    key: str = "global_company_selector",
) -> str | None:
    companies = list_companies()

    if not companies:
        st.warning("Сначала создайте хотя бы одну компанию в разделе Companies.")
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