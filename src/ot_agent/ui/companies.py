from __future__ import annotations

import streamlit as st

from ot_agent.db import company_exists, create_company, get_company, list_companies


def _format_company_option(company_id: str) -> str:
    company = get_company(company_id)

    if not company:
        return company_id

    legal_name = company.get("legal_name") or company_id
    return f"{legal_name} ({company_id})"


def _display_company(company: dict) -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.metric("company_id", company.get("company_id") or "—")
        st.metric("Юридическое наименование", company.get("legal_name") or "—")
        st.metric("Краткое наименование", company.get("short_name") or "—")
        st.metric("ИНН", company.get("inn") or "—")
        st.metric("КПП", company.get("kpp") or "—")
        st.metric("ОГРН", company.get("ogrn") or "—")

    with col2:
        st.metric("Статус", company.get("status") or "—")
        st.metric("Численность", str(company.get("headcount") if company.get("headcount") is not None else "—"))
        st.metric("Обособленные подразделения", "Да" if company.get("has_branches") else "Нет")
        st.metric(
            "Опасный производственный объект",
            "Да" if company.get("has_hazardous_production_facility") else "Нет",
        )
        st.metric("Код вида деятельности", company.get("industry_code") or "—")

    st.markdown("#### Адреса и контакты")

    col3, col4 = st.columns(2)

    with col3:
        st.write("**Юридический адрес:**")
        st.write(company.get("legal_address") or "—")

    with col4:
        st.write("**Фактический адрес:**")
        st.write(company.get("actual_address") or "—")

    st.write("**Телефон:**", company.get("phone") or "—")
    st.write("**Email:**", company.get("email") or "—")

    st.caption(
        "Все будущие реестры, должности, сотрудники, документы и правила "
        "будут фильтроваться по этому company_id."
    )


def render() -> None:
    st.subheader("Companies")

    companies = list_companies()

    if companies:
        company_ids = [company["company_id"] for company in companies]

        current_company_id = st.session_state.get("current_company_id")

        if current_company_id not in company_ids:
            current_company_id = company_ids[0]

        selected_company_id = st.selectbox(
            "Текущая компания",
            company_ids,
            index=company_ids.index(current_company_id),
            format_func=_format_company_option,
            key="company_selector",
        )

        st.session_state.current_company_id = selected_company_id

        selected_company = get_company(selected_company_id)

        if selected_company:
            _display_company(selected_company)
        else:
            st.error("Выбранная компания не найдена в базе данных.")
    else:
        st.warning("Компании пока не созданы. Создайте первую синтетическую компанию ниже.")

    st.markdown("---")

    with st.expander("Создать компанию", expanded=not companies):
        st.markdown(
            """
            Используйте только синтетические данные.  
            Не вносите реальные персональные данные работников.  
            """
        )

        with st.form("create_company_form"):
            company_id = st.text_input(
                "company_id *",
                help="Латиница, без пробелов. Например: LLC_TEST_ALPHA",
            )

            legal_name = st.text_input(
                "Юридическое наименование *",
                help="Например: ООО \"Тест Альфа\"",
            )

            short_name = st.text_input("Краткое наименование")
            inn = st.text_input("ИНН")
            kpp = st.text_input("КПП")
            ogrn = st.text_input("ОГРН")

            legal_address = st.text_area("Юридический адрес")
            actual_address = st.text_area("Фактический адрес")

            phone = st.text_input("Телефон")
            email = st.text_input("Email")
            industry_code = st.text_input("Код вида деятельности")

            headcount = st.number_input(
                "Численность",
                min_value=0,
                step=1,
                value=0,
            )

            has_branches = st.checkbox("Есть обособленные подразделения")
            has_hazardous_production_facility = st.checkbox(
                "Есть опасный производственный объект"
            )

            status = st.selectbox(
                "Статус компании",
                ["ACTIVE", "INACTIVE", "ARCHIVED"],
                index=0,
            )

            submitted = st.form_submit_button("Создать компанию")

            if submitted:
                clean_company_id = company_id.strip()
                clean_legal_name = legal_name.strip()

                if not clean_company_id:
                    st.error("Поле company_id обязательно.")
                elif not clean_legal_name:
                    st.error("Поле юридического наименования обязательно.")
                elif company_exists(clean_company_id):
                    st.error(
                        f"Компания с company_id={clean_company_id} уже существует."
                    )
                else:
                    try:
                        created = create_company(
                            {
                                "company_id": clean_company_id,
                                "legal_name": clean_legal_name,
                                "short_name": short_name,
                                "inn": inn,
                                "kpp": kpp,
                                "ogrn": ogrn,
                                "legal_address": legal_address,
                                "actual_address": actual_address,
                                "phone": phone,
                                "email": email,
                                "industry_code": industry_code,
                                "headcount": headcount,
                                "has_branches": has_branches,
                                "has_hazardous_production_facility": has_hazardous_production_facility,
                                "status": status,
                            }
                        )

                        st.success(
                            f"Компания создана: {created['legal_name']} "
                            f"({created['company_id']})"
                        )

                        st.session_state.current_company_id = created["company_id"]
                        st.rerun()

                    except Exception as exc:
                        st.error(f"Не удалось создать компанию: {exc}")