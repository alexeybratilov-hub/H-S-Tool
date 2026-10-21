from __future__ import annotations

import streamlit as st

from ot_agent import llm_client
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


def _model_name(model: dict) -> str:
    return str(model.get("name") or model.get("model") or "").strip()


def render() -> None:
    st.subheader("\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438")

    st.markdown(get_security_notice())

    st.markdown(
        """
        #### Приватность Streamlit

        Согласно политике конфиденциальности Streamlit, обновлённой в апреле 2026 года,
        Streamlit принадлежит Snowflake и регулируется Snowflake Privacy Notice.

        В этом проекте:
        - сбор статистики должен быть отключён;
        - реальные персональные данные не должны вводиться в тестовые поля;
        - запросы к LLM допускаются только на локальные адреса.
        """
    )

    cfg = load_app_settings()

    if not cfg:
        st.warning("Конфигурация не найдена.")
        return

    st.markdown("### Проверка локального режима")

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
        {
            "Параметр": "llm.secondary_model",
            "Значение": _get_nested(cfg, "llm", "secondary_model"),
        },
        {
            "Параметр": "llm.context_length",
            "Значение": _get_nested(cfg, "llm", "context_length"),
        },
        {
            "Параметр": "llm.temperature",
            "Значение": _get_nested(cfg, "llm", "temperature"),
        },
        {
            "Параметр": "llm.max_new_tokens",
            "Значение": _get_nested(cfg, "llm", "max_new_tokens"),
        },
    ]

    st.dataframe(rows, hide_index=True)

    st.markdown("---")
    st.markdown("### Локальное подключение к Ollama")

    st.caption(
        "Ниже выполняются только локальные HTTP-запросы к адресу из llm.base_url. "
        "Тестовый промпт не содержит персональных, медицинских или нормативных данных."
    )

    if st.button("Проверить список моделей", key="check_ollama_models"):
        try:
            models = llm_client.list_models()
            st.session_state["ollama_models"] = models

            if models:
                st.success(f"Ollama отвечает. Найдено моделей: {len(models)}")
            else:
                st.warning("Ollama отвечает, но список моделей пуст.")

        except Exception as exc:
            st.session_state.pop("ollama_models", None)
            st.error(f"Не удалось получить список моделей: {exc}")

    models = st.session_state.get("ollama_models") or []
    model_names = [_model_name(model) for model in models if _model_name(model)]

    primary_model = _get_nested(cfg, "llm", "primary_model")

    if model_names:
        default_index = (
            model_names.index(primary_model)
            if primary_model in model_names
            else 0
        )

        selected_model = st.selectbox(
            "Модель для технического теста",
            model_names,
            index=default_index,
            key="test_model_select",
        )
    else:
        selected_model = primary_model
        st.info(
            "Список моделей ещё не загружен. "
            "Тест будет использовать primary_model из конфигурации, "
            "если Ollama доступен."
        )

    test_disabled = (
        not selected_model
        or selected_model == "не задан"
        or selected_model == "REPLACE_AFTER_OLLAMA_LIST"
    )

    if st.button(
        "Выполнить технический тест генерации",
        key="test_llm_generate",
        disabled=test_disabled,
    ):
        with st.spinner(
            "Запрос к локальной модели. "
            "Первая загрузка модели в память может занимать время..."
        ):
            try:
                response, elapsed = llm_client.generate_test_response(selected_model)

                st.success(f"Тест выполнен за {elapsed:.1f} сек.")
                st.markdown("**Ответ модели:**")
                st.code(response, language="text")

            except Exception as exc:
                st.error(f"Тест не выполнен: {exc}")