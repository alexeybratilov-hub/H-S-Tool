import streamlit as st
from pathlib import Path

from ot_agent.drafts_db import (
    activate_rule,
    add_correction,
    add_version,
    create_draft,
    get_connection,
    get_draft,
    get_latest_diff,
    list_active_rules,
    list_companies,
    list_corrections,
    list_drafts,
    list_versions,
)

ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"

TITLE = "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a\u0438"
WARNING = (
    "\u0427\u0415\u0420\u041d\u041e\u0412\u0418\u041a / \u0411\u0415\u0417 LLM. "
    "\u0420\u0443\u0447\u043d\u043e\u0439 \u043a\u043e\u043d\u0442\u0443\u0440: \u0447\u0435\u0440\u043d\u043e\u0432\u0438\u043a "
    "\u2192 \u0432\u0435\u0440\u0441\u0438\u044f \u2192 \u0434\u0438\u0444\u0444 \u2192 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0430 "
    "\u2192 \u043f\u0440\u0430\u0432\u0438\u043b\u043e. \u0422\u0440\u0435\u0431\u0443\u0435\u0442 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438 \u0447\u0435\u043b\u043e\u0432\u0435\u043a\u043e\u043c."
)


def render_drafts() -> None:
    st.title(TITLE)
    st.warning(WARNING)

    conn = get_connection(DB_PATH)

    try:
        companies = list_companies(conn)

        if not companies:
            st.info("\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u0438 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b. \u0414\u043e\u0431\u0430\u0432\u044c\u0442\u0435 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u044e \u043d\u0430 \u0432\u043a\u043b\u0430\u0434\u043a\u0435 \u00ab\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u0438\u00bb.")
            return

        company_labels = [company["display_name"] for company in companies]
        company_ids = [company["company_id"] for company in companies]

        company_index = st.selectbox(
            "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f",
            range(len(company_labels)),
            format_func=lambda i: company_labels[i],
            key="draft_company_select",
        )

        company_id = company_ids[company_index]

        with st.expander("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0447\u0435\u0440\u043d\u043e\u0432\u0438\u043a"):
            title = st.text_input("\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", value="", key="draft_create_title")
            document_type = st.text_input("\u0422\u0438\u043f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430", value="", key="draft_create_doc_type")
            requirement_id = st.text_input("ID \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f (\u043d\u0435\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e)", value="", key="draft_create_req_id")
            initial_content = st.text_area("\u0418\u0441\u0445\u043e\u0434\u043d\u043e\u0435 \u0441\u043e\u0434\u0435\u0440\u0436\u0438\u043c\u043e\u0435", value="", key="draft_create_initial_content")

            if st.button("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0447\u0435\u0440\u043d\u043e\u0432\u0438\u043a", key="draft_create_button"):
                try:
                    draft_id = create_draft(
                        conn,
                        company_id=company_id,
                        title=title.strip() or "\u0411\u0435\u0437 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f",
                        document_type=document_type.strip() or None,
                        requirement_id=requirement_id.strip() or None,
                        initial_content=initial_content,
                    )
                    conn.commit()
                    st.success(f"\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e. draft_id={draft_id}")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        drafts = list_drafts(conn, company_id)

        if not drafts:
            st.info("\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a\u0438 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b.")
            return

        st.dataframe(drafts, hide_index=True, width="stretch")

        draft_labels = [
            f"{draft['draft_id']} | {draft['title']} | v{draft['current_version']}"
            for draft in drafts
        ]
        draft_ids = [draft["draft_id"] for draft in drafts]

        draft_index = st.selectbox(
            "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a",
            range(len(draft_labels)),
            format_func=lambda i: draft_labels[i],
            key="draft_select",
        )

        draft_id = draft_ids[draft_index]
        draft = get_draft(conn, draft_id)

        if not draft:
            st.error("\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.")
            return

        st.write("\u0422\u0435\u043a\u0443\u0449\u0430\u044f \u0432\u0435\u0440\u0441\u0438\u044f:", draft["current_version"])

        versions = list_versions(conn, draft_id)
        st.dataframe(versions, hide_index=True, width="stretch")

        with st.expander("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0432\u0435\u0440\u0441\u0438\u044e"):
            content = st.text_area("\u0421\u043e\u0434\u0435\u0440\u0436\u0438\u043c\u043e\u0435", value="", key="draft_add_version_content")
            author = st.text_input("\u0410\u0432\u0442\u043e\u0440", value="\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c", key="draft_add_version_author")
            comment = st.text_input("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439", value="", key="draft_add_version_comment")

            if st.button("\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0432\u0435\u0440\u0441\u0438\u044e", key="draft_add_version_button"):
                try:
                    version_number = add_version(
                        conn,
                        draft_id=draft_id,
                        content=content,
                        author=author.strip() or "\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c",
                        comment=comment.strip() or None,
                    )
                    conn.commit()
                    st.success(f"\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e. \u0412\u0435\u0440\u0441\u0438\u044f {version_number}")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        with st.expander("\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0439 \u0434\u0438\u0444\u0444"):
            diff = get_latest_diff(conn, draft_id)
            if diff and diff.get("diff_text"):
                st.code(diff["diff_text"])
            else:
                st.info("\u0414\u0438\u0444\u0444 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d.")

        with st.expander("\u041a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0438"):
            corrections = list_corrections(conn, draft_id)

            if corrections:
                st.dataframe(corrections, hide_index=True, width="stretch")

            current_version = int(draft["current_version"])

            from_version = st.number_input(
                "\u0418\u0437 \u0432\u0435\u0440\u0441\u0438\u0438",
                value=max(1, current_version - 1),
                min_value=1,
                step=1,
                key="draft_corr_from_version",
            )

            to_version = st.number_input(
                "\u0412 \u0432\u0435\u0440\u0441\u0438\u044e",
                value=current_version,
                min_value=1,
                step=1,
                key="draft_corr_to_version",
            )

            category = st.text_input("\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f", value="", key="draft_corr_category")
            old_snippet = st.text_area("\u0421\u0442\u0430\u0440\u044b\u0439 \u0444\u0440\u0430\u0433\u043c\u0435\u043d\u0442", value="", key="draft_corr_old_snippet")
            new_snippet = st.text_area("\u041d\u043e\u0432\u044b\u0439 \u0444\u0440\u0430\u0433\u043c\u0435\u043d\u0442", value="", key="draft_corr_new_snippet")
            correction_comment = st.text_input("\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439", value="", key="draft_corr_comment")
            proposed_rule = st.text_area("\u041f\u0440\u0435\u0434\u043b\u0430\u0433\u0430\u0435\u043c\u043e\u0435 \u043f\u0440\u0430\u0432\u0438\u043b\u043e", value="", key="draft_corr_proposed_rule")

            if st.button("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0443", key="draft_corr_save_button"):
                try:
                    correction_id = add_correction(
                        conn,
                        draft_id=draft_id,
                        from_version=int(from_version),
                        to_version=int(to_version),
                        category=category.strip() or None,
                        old_snippet=old_snippet.strip() or None,
                        new_snippet=new_snippet.strip() or None,
                        comment=correction_comment.strip() or None,
                        proposed_rule=proposed_rule.strip() or None,
                    )
                    conn.commit()
                    st.success(f"\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e. correction_id={correction_id}")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

            if corrections:
                correction_labels = [
                    f"{c['correction_id']} | {c['status']} | {c['category'] or ''}"
                    for c in corrections
                ]
                correction_ids = [c["correction_id"] for c in corrections]

                correction_index = st.selectbox(
                    "\u041a\u043e\u0440\u0440\u0435\u043a\u0442\u0438\u0440\u043e\u0432\u043a\u0430",
                    range(len(correction_labels)),
                    format_func=lambda i: correction_labels[i],
                    key="draft_corr_select",
                )

                if st.button("\u0410\u043a\u0442\u0438\u0432\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u0440\u0430\u0432\u0438\u043b\u043e", key="draft_corr_activate_button"):
                    try:
                        rule_id = activate_rule(
                            conn,
                            correction_ids[correction_index],
                        )
                        conn.commit()
                        st.success(f"\u0410\u043a\u0442\u0438\u0432\u0438\u0440\u043e\u0432\u0430\u043d\u043e. rule_id={rule_id}")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

        with st.expander("\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u043f\u0440\u0430\u0432\u0438\u043b\u0430"):
            rules = list_active_rules(conn, company_id=company_id, topic="OT")

            if rules:
                st.dataframe(rules, hide_index=True, width="stretch")
            else:
                st.info("\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0445 \u043f\u0440\u0430\u0432\u0438\u043b \u043d\u0435\u0442.")

    finally:
        conn.close()


render = render_drafts

# STAGE13_DRAFT_UI_FIX_BEGIN
def _s13_field(row, key, default=""):
    try:
        if hasattr(row, "get"):
            value = row.get(key, default)
        else:
            keys = list(row.keys())
            value = row[key] if key in keys else default
    except Exception:
        value = default

    return default if value is None else value


def _s13_draft_count(conn, company_id):
    if not company_id:
        return 0

    try:
        return int(
            conn.execute(
                "SELECT COUNT(*) FROM drafts WHERE company_id = ?",
                (company_id,),
            ).fetchone()[0]
            or 0
        )
    except Exception:
        return 0


_orig_list_companies_s13 = globals().get("list_companies")


def list_companies(conn):
    if not callable(_orig_list_companies_s13):
        return []

    rows = list(_orig_list_companies_s13(conn))
    ranked = []

    for row in rows:
        company_id = _s13_field(row, "company_id", "")
        ranked.append((_s13_draft_count(conn, company_id), row))

    ranked.sort(
        key=lambda item: (
            -item[0],
            str(
                _s13_field(
                    item[1],
                    "display_name",
                    _s13_field(item[1], "company_id", ""),
                )
            ),
        )
    )

    return [row for _count, row in ranked]


_orig_render_drafts_s13 = globals().get("render_drafts")


if callable(_orig_render_drafts_s13):
    def render_drafts():
        try:
            import streamlit as st
            from ot_agent.drafts_db import get_connection as _s13_get_connection

            conn = _s13_get_connection()

            try:
                rows = list_companies(conn)
                counts = []

                for row in rows:
                    company_id = _s13_field(row, "company_id", "")
                    display_name = _s13_field(row, "display_name", company_id)
                    count = _s13_draft_count(conn, company_id)
                    counts.append(
                        {
                            "company_id": company_id,
                            "display_name": display_name,
                            "drafts": count,
                        }
                    )
            finally:
                conn.close()

            if counts:
                st.caption(
                    "\u042d\u0442\u0430\u043f 13: \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438 \u0441 \u0447\u0435\u0440\u043d\u043e\u0432\u0438\u043a\u0430\u043c\u0438 \u043e\u0442\u0441\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u044b \u043f\u0435\u0440\u0432\u044b\u043c\u0438."
                )
        except Exception:
            pass

        _orig_render_drafts_s13()

    render = render_drafts
# STAGE13_DRAFT_UI_FIX_END