from __future__ import annotations

import pandas as pd
import streamlit as st

from ot_agent.applicability_db import (
    ALLOWED_APPLICABILITY_STATUSES,
    count_applicability,
    list_sources_with_applicability,
    upsert_applicability,
)
from ot_agent.regulatory_db import list_sources
from ot_agent.security import get_security_notice
from ot_agent.ui.common import render_company_selector


STATUS_ORDER = [
    "SUGGESTED",
    "CONFIRMED",
    "REJECTED",
    "REQUIRES_VERIFICATION",
]


def _rows_to_dataframe(
    rows: list[dict[str, object]],
    columns: list[str],
) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=columns)

    cleaned_rows = []

    for row in rows:
        cleaned = {}

        for column in columns:
            value = row.get(column)

            if value is None:
                cleaned[column] = ""
            else:
                cleaned[column] = str(value)

        cleaned_rows.append(cleaned)

    return pd.DataFrame(cleaned_rows, columns=columns)


def render() -> None:
    st.subheader("Norm Applicability")

    st.markdown(get_security_notice())

    st.caption(
        "\u041f\u0440\u0438\u043c\u0435\u043d\u0438\u043c\u043e\u0441\u0442\u044c "
        "\u043d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u044b\u0445 "
        "\u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u0432 \u043a "
        "\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438. "
        "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0430\u0435\u0442 "
        "\u0442\u043e\u043b\u044c\u043a\u043e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c. "
        "\u0421\u0438\u043d\u0442\u0435\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0435 "
        "\u043d\u043e\u0440\u043c\u044b \u043d\u0435 \u044f\u0432\u043b\u044f\u044e\u0442\u0441\u044f "
        "\u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u0438\u043c \u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u043c."
    )

    company_id = render_company_selector(key="applicability_company_selector")

    if not company_id:
        return

    counts = count_applicability(company_id)

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total", counts.get("total", 0))
    col2.metric("Confirmed", counts.get("CONFIRMED", 0))
    col3.metric("Suggested", counts.get("SUGGESTED", 0))
    col4.metric("Rejected", counts.get("REJECTED", 0))
    col5.metric("Requires verification", counts.get("REQUIRES_VERIFICATION", 0))

    st.caption(f"Company: {company_id}")

    rows = list_sources_with_applicability(company_id)

    columns = [
        "source_id",
        "source_title",
        "source_status",
        "source_verification_status",
        "applicability_status",
        "reason",
        "confirmed_by",
        "confirmed_at",
    ]

    st.dataframe(
        _rows_to_dataframe(rows, columns),
        hide_index=True,
        width="stretch",
    )

    st.markdown("---")
    st.markdown("### Change applicability")

    sources = list_sources()

    if not sources:
        st.warning(
            "\u041d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u044b\u0435 "
            "\u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u0438 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b."
        )
        return

    source_options = [str(source["source_id"]) for source in sources]

    labels = {
        str(source["source_id"]): (
            f"{source.get('title') or source['source_id']} "
            f"({source['source_id']})"
        )
        for source in sources
    }

    selected_source_id = st.selectbox(
        "Source",
        source_options,
        format_func=lambda source_id: labels.get(source_id, source_id),
        key="applicability_source_selector",
    )

    current_by_source = {
        str(row.get("source_id")): row
        for row in rows
    }

    current = current_by_source.get(selected_source_id, {})

    current_status = str(current.get("applicability_status") or "REQUIRES_VERIFICATION")

    if current_status not in ALLOWED_APPLICABILITY_STATUSES:
        current_status = "REQUIRES_VERIFICATION"

    status_index = STATUS_ORDER.index(current_status)

    applicability_status = st.selectbox(
        "Applicability status",
        STATUS_ORDER,
        index=status_index,
        key="applicability_status_select",
    )

    reason = st.text_area(
        "Reason",
        value=str(current.get("reason") or ""),
        key="applicability_reason",
    )

    confirmed_by = st.text_input(
        "Confirmed by",
        value=str(current.get("confirmed_by") or "TEST_USER"),
        key="applicability_confirmed_by",
    )

    if st.button("Save applicability", key="save_applicability_button"):
        try:
            saved = upsert_applicability(
                {
                    "company_id": company_id,
                    "source_id": selected_source_id,
                    "chunk_id": "",
                    "applicability_status": applicability_status,
                    "reason": reason,
                    "confirmed_by": confirmed_by,
                }
            )

            st.success(
                "Saved: "
                f"{saved['company_id']} | "
                f"{saved['source_id']} | "
                f"{saved['applicability_status']}"
            )

            st.rerun()

        except Exception as exc:
            st.error(f"Save failed: {exc}")