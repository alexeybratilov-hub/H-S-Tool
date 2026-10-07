from __future__ import annotations

import streamlit as st

from ot_agent.config import load_app_settings
from ot_agent.security import get_security_notice


def _get_nested(config: dict, *keys: str) -> str:
    value = config

    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return "не задан"

    if value is None:
        return "не задан"

    return str(value)


def render() -> None:
    st.subheader("Settings")

    st.markdown(get_security_notice())

    cfg = load_app_settings()

    if not cfg:
        st.warning("Конфигурация не найдена.")
        return

    st.write("Проверка локального режима:")

    rows = [
        {
            "Параметр": "app.mode",
            "Значение": _get_nested(cfg, "app", "mode"),
        },
        {
            "Параметр": "security.bind_address",
            "Значение": _get_nested(cfg, "security", "bind_address"),
        },
        {
            "Параметр": "security.allow_cloud",
            "Значение": _get_nested(cfg, "security", "allow_cloud"),
        },
        {
            "Параметр": "security.allow_auto_send",
            "Значение": _get_nested(cfg, "security", "allow_auto_send"),
        },
        {
            "Параметр": "llm.provider",
            "Значение": _get_nested(cfg, "llm", "provider"),
        },
        {
            "Параметр": "llm.base_url",
            "Значение": _get_nested(cfg, "llm", "base_url"),
        },
        {
            "Параметр": "llm.primary_model",
            "Значение": _get_nested(cfg, "llm", "primary_model"),
        },
    ]

    st.dataframe(rows, hide_index=True)