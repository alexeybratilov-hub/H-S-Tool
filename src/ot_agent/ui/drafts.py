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
    "DRAFT / NO_LLM. "
    "Synthetic manual draft/version/diff/corrections/rules pipeline. "
    "Requires human verification."
)


def render_drafts() -> None:
    st.title(TITLE)
    st.warning(WARNING)

    conn = get_connection(DB_PATH)

    try:
        companies = list_companies(conn)

        if not companies:
            st.info("No companies found.")
            return

        company_labels = [company["display_name"] for company in companies]
        company_ids = [company["company_id"] for company in companies]

        company_index = st.selectbox(
            "Company",
            range(len(company_labels)),
            format_func=lambda i: company_labels[i],
            key="draft_company_select",
        )

        company_id = company_ids[company_index]

        with st.expander("Create draft"):
            title = st.text_input("Title", value="", key="draft_create_title")
            document_type = st.text_input("Document type", value="", key="draft_create_doc_type")
            requirement_id = st.text_input("Requirement ID (optional)", value="", key="draft_create_req_id")
            initial_content = st.text_area("Initial content", value="", key="draft_create_initial_content")

            if st.button("Create draft", key="draft_create_button"):
                try:
                    draft_id = create_draft(
                        conn,
                        company_id=company_id,
                        title=title.strip() or "Untitled draft",
                        document_type=document_type.strip() or None,
                        requirement_id=requirement_id.strip() or None,
                        initial_content=initial_content,
                    )
                    conn.commit()
                    st.success(f"Saved. draft_id={draft_id}")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        drafts = list_drafts(conn, company_id)

        if not drafts:
            st.info("No drafts found.")
            return

        st.dataframe(drafts, hide_index=True, width="stretch")

        draft_labels = [
            f"{draft['draft_id']} | {draft['title']} | v{draft['current_version']}"
            for draft in drafts
        ]
        draft_ids = [draft["draft_id"] for draft in drafts]

        draft_index = st.selectbox(
            "Draft",
            range(len(draft_labels)),
            format_func=lambda i: draft_labels[i],
            key="draft_select",
        )

        draft_id = draft_ids[draft_index]
        draft = get_draft(conn, draft_id)

        if not draft:
            st.error("Draft not found.")
            return

        st.write("Current version:", draft["current_version"])

        versions = list_versions(conn, draft_id)
        st.dataframe(versions, hide_index=True, width="stretch")

        with st.expander("Add version"):
            content = st.text_area("Content", value="", key="draft_add_version_content")
            author = st.text_input("Author", value="user", key="draft_add_version_author")
            comment = st.text_input("Comment", value="", key="draft_add_version_comment")

            if st.button("Add version", key="draft_add_version_button"):
                try:
                    version_number = add_version(
                        conn,
                        draft_id=draft_id,
                        content=content,
                        author=author.strip() or "user",
                        comment=comment.strip() or None,
                    )
                    conn.commit()
                    st.success(f"Saved. v{version_number}")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        with st.expander("Latest diff"):
            diff = get_latest_diff(conn, draft_id)
            if diff and diff.get("diff_text"):
                st.code(diff["diff_text"])
            else:
                st.info("No diff available.")

        with st.expander("Corrections"):
            corrections = list_corrections(conn, draft_id)

            if corrections:
                st.dataframe(corrections, hide_index=True, width="stretch")

            current_version = int(draft["current_version"])

            from_version = st.number_input(
                "From version",
                value=max(1, current_version - 1),
                min_value=1,
                step=1,
                key="draft_corr_from_version",
            )

            to_version = st.number_input(
                "To version",
                value=current_version,
                min_value=1,
                step=1,
                key="draft_corr_to_version",
            )

            category = st.text_input("Category", value="", key="draft_corr_category")
            old_snippet = st.text_area("Old snippet", value="", key="draft_corr_old_snippet")
            new_snippet = st.text_area("New snippet", value="", key="draft_corr_new_snippet")
            correction_comment = st.text_input("Comment", value="", key="draft_corr_comment")
            proposed_rule = st.text_area("Proposed rule", value="", key="draft_corr_proposed_rule")

            if st.button("Save correction", key="draft_corr_save_button"):
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
                    st.success(f"Saved. correction_id={correction_id}")
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
                    "Correction",
                    range(len(correction_labels)),
                    format_func=lambda i: correction_labels[i],
                    key="draft_corr_select",
                )

                if st.button("Activate rule", key="draft_corr_activate_button"):
                    try:
                        rule_id = activate_rule(
                            conn,
                            correction_ids[correction_index],
                        )
                        conn.commit()
                        st.success(f"Activated. rule_id={rule_id}")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

        with st.expander("Active rules"):
            rules = list_active_rules(conn, company_id=company_id, topic="OT")

            if rules:
                st.dataframe(rules, hide_index=True, width="stretch")
            else:
                st.info("No active rules.")

    finally:
        conn.close()


render = render_drafts
