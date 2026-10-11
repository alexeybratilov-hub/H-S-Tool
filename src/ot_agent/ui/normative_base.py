from __future__ import annotations

import pandas as pd
import streamlit as st

from ot_agent.regulatory_db import (
    count_regulatory,
    list_chunks,
    list_sources,
    search_norms,
)
from ot_agent.security import get_security_notice


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


def _snippet(text: str, max_len: int = 180) -> str:
    text = " ".join(str(text or "").split())

    if len(text) <= max_len:
        return text

    return text[: max_len - 3] + "..."


def render() -> None:
    st.subheader("\u041d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u0430\u044f \u0431\u0430\u0437\u0430")

    st.markdown(get_security_notice())

    st.caption(
        "\u0421\u0438\u043d\u0442\u0435\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0435 "
        "\u043d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u044b\u0435 "
        "\u0444\u0440\u0430\u0433\u043c\u0435\u043d\u0442\u044b. "
        "\u041d\u0435 \u044f\u0432\u043b\u044f\u044e\u0442\u0441\u044f "
        "\u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u0438\u043c "
        "\u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u043c."
    )

    counts = count_regulatory()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u0438",
        counts.get("sources", 0),
    )

    col2.metric(
        "\u0424\u0440\u0430\u0433\u043c\u0435\u043d\u0442\u044b",
        counts.get("chunks", 0),
    )

    col3.metric(
        "\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u0438 \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435",
        counts.get("requires_verification_sources", 0),
    )

    col4.metric(
        "\u0424\u0440\u0430\u0433\u043c\u0435\u043d\u0442\u044b \u043d\u0430 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0435",
        counts.get("requires_verification_chunks", 0),
    )

    query = st.text_input(
        "\u041f\u043e\u0438\u0441\u043a \u043f\u043e \u043a\u043b\u044e\u0447\u0435\u0432\u044b\u043c \u0441\u043b\u043e\u0432\u0430\u043c",
        key="normative_search_query",
    )

    results = search_norms(query, limit=100)

    if results:
        display_rows = []

        for row in results:
            display_rows.append(
                {
                    "source_id": row.get("source_id", ""),
                    "source_title": row.get("source_title", ""),
                    "source_status": row.get("source_status", ""),
                    "verification_status": row.get("verification_status", ""),
                    "chunk_id": row.get("chunk_id", ""),
                    "heading_path": row.get("heading_path", ""),
                    "keywords": row.get("keywords", ""),
                    "confidence_tag": row.get("confidence_tag", ""),
                    "snippet": _snippet(str(row.get("text", ""))),
                }
            )

        st.dataframe(
            _rows_to_dataframe(
                display_rows,
                [
                    "source_id",
                    "source_title",
                    "source_status",
                    "verification_status",
                    "chunk_id",
                    "heading_path",
                    "keywords",
                    "confidence_tag",
                    "snippet",
                ],
            ),
            hide_index=True,
            width="stretch",
        )
    else:
        st.info(
            "\u041d\u0435\u0442 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u043e\u0432 "
            "\u043f\u043e\u0438\u0441\u043a\u0430."
        )

    st.markdown("---")

    with st.expander(
        "\u041f\u043e\u043b\u043d\u044b\u0439 \u0441\u043f\u0438\u0441\u043e\u043a \u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u0432",
        expanded=False,
    ):
        sources = list_sources()

        if not sources:
            st.warning(
                "\u041d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u044b\u0435 "
                "\u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u0438 \u0435\u0449\u0451 "
                "\u043d\u0435 \u0437\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u044b."
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
            "\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a",
            source_options,
            format_func=lambda source_id: labels.get(source_id, source_id),
            key="normative_source_selector",
        )

        chunks = list_chunks(selected_source_id)

        if not chunks:
            st.info(
                "\u0423 \u0432\u044b\u0431\u0440\u0430\u043d\u043d\u043e\u0433\u043e "
                "\u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u0430 \u043d\u0435\u0442 "
                "\u0444\u0440\u0430\u0433\u043c\u0435\u043d\u0442\u043e\u0432."
            )
            return

        chunk_rows = []

        for chunk in chunks:
            chunk_rows.append(
                {
                    "chunk_id": chunk.get("chunk_id", ""),
                    "heading_path": chunk.get("heading_path", ""),
                    "chunk_index": chunk.get("chunk_index", ""),
                    "status": chunk.get("status", ""),
                    "confidence_tag": chunk.get("confidence_tag", ""),
                    "keywords": chunk.get("keywords", ""),
                    "text": chunk.get("text", ""),
                }
            )

        st.dataframe(
            _rows_to_dataframe(
                chunk_rows,
                [
                    "chunk_id",
                    "heading_path",
                    "chunk_index",
                    "status",
                    "confidence_tag",
                    "keywords",
                    "text",
                ],
            ),
            hide_index=True,
            width="stretch",
        )