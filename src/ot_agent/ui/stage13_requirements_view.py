import pandas as pd
import streamlit as st

from ot_agent.ppe_sout_risk_db import DB_PATH, get_connection

try:
    from ot_agent.stage13_confirmed_package_db import (
        apply_sync,
        get_connection as get_sync_connection,
        plan_sync,
        summary,
        validate_sync,
    )

    SYNC_MODULE_AVAILABLE = True
    SYNC_IMPORT_ERROR = ""
except Exception as _sync_exc:
    SYNC_MODULE_AVAILABLE = False
    SYNC_IMPORT_ERROR = str(_sync_exc)

    apply_sync = None
    get_sync_connection = None
    plan_sync = None
    summary = None
    validate_sync = None

try:
    from ot_agent.stage13_drafts_db import (
        create_draft_from_requirement,
        get_connection as get_draft_connection,
    )

    DRAFT_MODULE_AVAILABLE = True
    DRAFT_IMPORT_ERROR = ""
except Exception as _draft_exc:
    DRAFT_MODULE_AVAILABLE = False
    DRAFT_IMPORT_ERROR = str(_draft_exc)

    create_draft_from_requirement = None
    get_draft_connection = None

SOURCE_TYPE = "STAGE13_PRELIMINARY"
ALLOWED_STATUSES = ("CONFIRMED", "REJECTED", "REQUIRES_VERIFICATION")
BENIGN_ISSUE_PREFIXES = (
    "suggestion already transferred:",
)

HEADER = "\u041f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f \u042d\u0442\u0430\u043f\u0430 13"
NOTE = "\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u044f. \u041d\u0435 \u044f\u0432\u043b\u044f\u044e\u0442\u0441\u044f \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d\u043d\u044b\u043c \u043f\u0435\u0440\u0435\u0447\u043d\u0435\u043c."
ACTION_NOTE = "\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u0435/\u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d\u0438\u0435 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u043c. \u041d\u0435 \u044f\u0432\u043b\u044f\u0435\u0442\u0441\u044f \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u0438\u043c \u0437\u0430\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435\u043c."
COMPANY = "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u044f"
STATUS = "\u0421\u0442\u0430\u0442\u0443\u0441"
ALL = "\u0412\u0441\u0435"
SEARCH = "\u041f\u043e\u0438\u0441\u043a"
TOTAL = "\u0412\u0441\u0435\u0433\u043e"
REQUIREMENT = "\u0417\u0430\u043f\u0438\u0441\u044c"
ACTIONS = "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u044f"
CONFIRM = "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438"
REJECT = "\u041e\u0442\u043a\u043b\u043e\u043d\u0438\u0442\u044c \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438"
RESET = "\u0412\u0435\u0440\u043d\u0443\u0442\u044c \u0432 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0443"
SAVED = "\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e"
SAVE_ERROR = "\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u044f"
NO_COMPANIES = "\u041d\u0435\u0442 \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0439"
NO_ROWS = "\u041d\u0435\u0442 \u043f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0445 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u0439"
QUERY_ERROR = "\u041e\u0448\u0438\u0431\u043a\u0430 \u0437\u0430\u043f\u0440\u043e\u0441\u0430"

SYNC_HEADER = "\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u044f \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d\u043d\u044b\u0445 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u0439"
SYNC_NOTE = "\u0421\u043e\u0437\u0434\u0430\u0451\u0442 \u0438\u043b\u0438 \u043e\u0431\u043d\u043e\u0432\u043b\u044f\u0435\u0442 \u0447\u0435\u0440\u043d\u043e\u0432\u044b\u0435 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u043f\u0430\u043a\u0435\u0442\u044b PKG:S13_CONFIRMED. \u041d\u0435 \u044f\u0432\u043b\u044f\u0435\u0442\u0441\u044f \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u0438\u043c \u0443\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u0435\u043c."
SYNC_MODULE_UNAVAILABLE = "\u041c\u043e\u0434\u0443\u043b\u044c \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u0438 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d"
SYNC_PREVIEW_ERROR = "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u043f\u0440\u0435\u0434\u0432\u0430\u0440\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435"
SYNC_PLAN_ERRORS = "\u0421\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u044f \u043d\u0435 \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430: \u043d\u0430\u0439\u0434\u0435\u043d\u044b \u043f\u0440\u043e\u0431\u043b\u0435\u043c\u044b"
SYNC_INFO_ISSUES = "\u0418\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u043e\u043d\u043d\u044b\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u044f \u043f\u043b\u0430\u043d\u0438\u0440\u043e\u0432\u0449\u0438\u043a\u0430"
SYNC_AGREE = "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0430\u044e \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0443\u044e \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u044e (\u043d\u0435 \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u0443\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u0435)"
SYNC_BUTTON = "\u0421\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d\u043d\u044b\u0435 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f"
SYNC_SUCCESS = "\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u044f \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u0430"
SYNC_VALIDATION_ERRORS = "\u0421\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u044f \u043e\u0442\u043c\u0435\u043d\u0435\u043d\u0430: \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043d\u0435 \u043f\u0440\u043e\u0439\u0434\u0435\u043d\u0430"
SYNC_EXECUTION_ERROR = "\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u0438"
METRIC_CONFIRMED = "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d\u043d\u044b\u0435 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f"
METRIC_PACKAGES = "\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u043f\u0430\u043a\u0435\u0442\u044b"
METRIC_ITEMS = "\u041f\u043e\u0437\u0438\u0446\u0438\u0438 \u043f\u0430\u043a\u0435\u0442\u043e\u0432"
METRIC_ADD = "\u0411\u0443\u0434\u0435\u0442 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043e \u043f\u043e\u0437\u0438\u0446\u0438\u0439"
METRIC_REMOVE = "\u0411\u0443\u0434\u0435\u0442 \u0443\u0434\u0430\u043b\u0435\u043d\u043e \u043f\u043e\u0437\u0438\u0446\u0438\u0439"

DRAFT_SECTION = "\u0414\u0435\u0439\u0441\u0442\u0432\u0438\u044f \u0441 \u0447\u0435\u0440\u043d\u043e\u0432\u0438\u043a\u043e\u043c"
DRAFT_NOTE = "\u0421\u043e\u0437\u0434\u0430\u0451\u0442 \u043b\u043e\u043a\u0430\u043b\u044c\u043d\u044b\u0439 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0447\u0435\u0440\u043d\u043e\u0432\u0438\u043a. \u0411\u0435\u0437 LLM, \u0431\u0435\u0437 DOCX, \u0431\u0435\u0437 \u044e\u0440\u0438\u0434\u0438\u0447\u0435\u0441\u043a\u043e\u0433\u043e \u0443\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0438\u044f."
CREATE_DRAFT = "\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0447\u0435\u0440\u043d\u043e\u0432\u0438\u043a"
DRAFT_CREATED = "\u0427\u0435\u0440\u043d\u043e\u0432\u0438\u043a \u0441\u043e\u0437\u0434\u0430\u043d"
DRAFT_ERROR = "\u041e\u0448\u0438\u0431\u043a\u0430 \u0441\u043e\u0437\u0434\u0430\u043d\u0438\u044f \u0447\u0435\u0440\u043d\u043e\u0432\u0438\u043a\u0430"
DRAFT_NOT_CONFIRMED = "\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u043e \u0442\u043e\u043b\u044c\u043a\u043e \u0434\u043b\u044f \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0438 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d\u043d\u044b\u0445 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u0439."
DRAFT_MODULE_UNAVAILABLE = "\u041c\u043e\u0434\u0443\u043b\u044c \u0447\u0435\u0440\u043d\u043e\u0432\u0438\u043a\u043e\u0432 \u042d\u0442\u0430\u043f\u0430 13 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d"


def _safe_key(value: object) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in str(value))


def _df(sql, params=()):
    conn = get_connection(DB_PATH)

    try:
        if params:
            cur = conn.execute(sql, params)
        else:
            cur = conn.execute(sql)

        cols = [d[0] for d in cur.description]
        rows = [tuple(r) for r in cur.fetchall()]
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()


def _update_status(requirement_id: str, company_id: str, new_status: str) -> None:
    if new_status not in ALLOWED_STATUSES:
        raise ValueError("unsupported status")

    conn = get_connection(DB_PATH)

    try:
        cur = conn.cursor()

        row = cur.execute(
            """
            SELECT company_id, source_type, status
            FROM document_requirements
            WHERE requirement_id = ?
            """,
            (requirement_id,),
        ).fetchone()

        if row is None:
            raise ValueError("record not found")

        if row["company_id"] != company_id:
            raise ValueError("company mismatch")

        if row["source_type"] != SOURCE_TYPE:
            raise ValueError("not stage13 preliminary record")

        company = cur.execute(
            "SELECT 1 FROM companies WHERE company_id = ?",
            (company_id,),
        ).fetchone()

        if company is None:
            raise ValueError("company not found")

        cur.execute(
            """
            UPDATE document_requirements
            SET status = ?, updated_at = datetime('now')
            WHERE requirement_id = ?
              AND company_id = ?
              AND source_type = ?
            """,
            (new_status, requirement_id, company_id, SOURCE_TYPE),
        )

        if cur.rowcount != 1:
            conn.rollback()
            raise ValueError("update affected unexpected rows")

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def _blocking_issues(issues):
    return [
        issue
        for issue in issues
        if not str(issue).startswith(BENIGN_ISSUE_PREFIXES)
    ]


def _informational_issues(issues):
    blocking = set(_blocking_issues(issues))
    return [issue for issue in issues if issue not in blocking]


def _sync_preview():
    if not SYNC_MODULE_AVAILABLE:
        return None, [SYNC_IMPORT_ERROR or SYNC_MODULE_UNAVAILABLE]

    conn = get_sync_connection()

    try:
        (
            packages_to_create,
            packages_to_remove,
            items_to_add,
            items_to_remove,
            confirmed_ids,
            issues,
        ) = plan_sync(conn)

        stats = summary(conn)

        preview = {
            "confirmed": len(confirmed_ids),
            "packages": int(stats.get("technical_packages", 0) or 0),
            "items": int(stats.get("technical_package_items", 0) or 0),
            "packages_create": len(packages_to_create),
            "packages_remove": len(packages_to_remove),
            "items_add": len(items_to_add),
            "items_remove": len(items_to_remove),
            "issues": list(issues),
        }

        return preview, []

    except Exception as exc:
        return None, [str(exc)]

    finally:
        conn.close()


def _perform_sync():
    if not SYNC_MODULE_AVAILABLE:
        return False, [SYNC_IMPORT_ERROR or SYNC_MODULE_UNAVAILABLE], None

    conn = get_sync_connection()

    try:
        (
            packages_to_create,
            packages_to_remove,
            items_to_add,
            items_to_remove,
            _confirmed_ids,
            issues,
        ) = plan_sync(conn)

        blocking = _blocking_issues(issues)

        if blocking:
            conn.rollback()
            return False, blocking, None

        stats = apply_sync(
            conn,
            packages_to_create,
            packages_to_remove,
            items_to_add,
            items_to_remove,
        )

        validation_errors = validate_sync(conn)

        if validation_errors:
            conn.rollback()
            return False, validation_errors, None

        conn.commit()
        return True, [], stats

    except Exception as exc:
        conn.rollback()
        return False, [str(exc)], None

    finally:
        conn.close()


def _create_draft(requirement_id: str, company_id: str) -> dict:
    if not DRAFT_MODULE_AVAILABLE:
        raise RuntimeError(DRAFT_IMPORT_ERROR or DRAFT_MODULE_UNAVAILABLE)

    conn = get_draft_connection()

    try:
        return create_draft_from_requirement(
            conn,
            company_id=company_id,
            requirement_id=requirement_id,
            author="streamlit_user",
            comment="Created from Stage 13 technical confirmation.",
            commit=True,
        )
    finally:
        conn.close()


def render_stage13_requirements():
    st.header(HEADER)
    st.caption(NOTE)

    try:
        companies = _df("SELECT company_id FROM companies ORDER BY company_id")
    except Exception as exc:
        st.error(f"{QUERY_ERROR}: {exc}")
        return

    if companies.empty:
        st.info(NO_COMPANIES)
        return

    company_id = st.selectbox(
        COMPANY,
        companies["company_id"].tolist(),
        key="s13_req_company",
    )

    try:
        rows = _df(
            """
            SELECT *
            FROM document_requirements
            WHERE company_id = ?
              AND source_type = ?
            ORDER BY code, title
            """,
            (company_id, SOURCE_TYPE),
        )
    except Exception as exc:
        st.error(f"{QUERY_ERROR}: {exc}")
        rows = pd.DataFrame()

    if rows.empty:
        st.info(NO_ROWS)
    else:
        if "status" in rows.columns:
            counts = rows["status"].astype(str).value_counts().to_dict()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(TOTAL, len(rows))
            c2.metric("REQUIRES_VERIFICATION", counts.get("REQUIRES_VERIFICATION", 0))
            c3.metric("CONFIRMED", counts.get("CONFIRMED", 0))
            c4.metric("REJECTED", counts.get("REJECTED", 0))

        col1, col2 = st.columns(2)

        search = col1.text_input(
            SEARCH,
            key="s13_req_search",
        )

        status_values = [ALL]

        if "status" in rows.columns:
            status_values += sorted(
                {str(v) for v in rows["status"].dropna().tolist() if str(v)}
            )

        selected_status = col2.selectbox(
            STATUS,
            status_values,
            key="s13_req_status",
        )

        view = rows

        if search:
            mask = pd.Series(False, index=view.index)

            for c in view.columns:
                if view[c].dtype == object:
                    mask |= view[c].astype(str).str.contains(search, case=False, na=False)

            view = view[mask]

        if "status" in view.columns and selected_status != ALL:
            view = view[view["status"].astype(str) == selected_status]

        if view.empty:
            st.info(NO_ROWS)
        else:
            st.dataframe(view)

        st.markdown(f"**{ACTIONS}**")
        st.caption(ACTION_NOTE)

        if "requirement_id" not in rows.columns:
            st.info(NO_ROWS)
        else:
            ids = []
            labels = []

            for _, row in rows.iterrows():
                rid = str(row.get("requirement_id", "")).strip()

                if not rid:
                    continue

                code = str(row.get("code", ""))
                title = str(row.get("title", ""))
                status = str(row.get("status", ""))

                ids.append(rid)
                labels.append(f"{code} | {title} | {status}")

            if not ids:
                st.info(NO_ROWS)
            else:
                idx = st.selectbox(
                    REQUIREMENT,
                    range(len(ids)),
                    format_func=lambda i: labels[i],
                    key="s13_req_action",
                )

                rid = ids[idx]
                safe_rid = _safe_key(rid)
                selected_row = rows.iloc[idx]
                selected_req_status = str(selected_row.get("status", ""))

                b1, b2, b3 = st.columns(3)

                if b1.button(CONFIRM, key=f"s13_confirm_{safe_rid}"):
                    try:
                        _update_status(rid, company_id, "CONFIRMED")
                        st.success(SAVED)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"{SAVE_ERROR}: {exc}")

                if b2.button(REJECT, key=f"s13_reject_{safe_rid}"):
                    try:
                        _update_status(rid, company_id, "REJECTED")
                        st.success(SAVED)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"{SAVE_ERROR}: {exc}")

                if b3.button(RESET, key=f"s13_reset_{safe_rid}"):
                    try:
                        _update_status(rid, company_id, "REQUIRES_VERIFICATION")
                        st.success(SAVED)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"{SAVE_ERROR}: {exc}")

                st.markdown(f"**{DRAFT_SECTION}**")
                st.caption(DRAFT_NOTE)

                if not DRAFT_MODULE_AVAILABLE:
                    st.error(f"{DRAFT_MODULE_UNAVAILABLE}: {DRAFT_IMPORT_ERROR}")
                else:
                    if selected_req_status != "CONFIRMED":
                        st.info(DRAFT_NOT_CONFIRMED)

                    if st.button(
                        CREATE_DRAFT,
                        key=f"s13_create_draft_{safe_rid}",
                        disabled=(selected_req_status != "CONFIRMED"),
                    ):
                        try:
                            result = _create_draft(rid, company_id)
                            st.success(DRAFT_CREATED)
                            st.json(result)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"{DRAFT_ERROR}: {exc}")

    st.markdown("---")
    st.subheader(SYNC_HEADER)
    st.caption(SYNC_NOTE)

    if not SYNC_MODULE_AVAILABLE:
        st.error(f"{SYNC_MODULE_UNAVAILABLE}: {SYNC_IMPORT_ERROR}")
        return

    preview, preview_errors = _sync_preview()

    if preview_errors:
        st.error(SYNC_PREVIEW_ERROR)

        for error in preview_errors[:30]:
            st.write(error)

        return

    if preview is None:
        st.error(SYNC_PREVIEW_ERROR)
        return

    blocking = _blocking_issues(preview["issues"])
    informational = _informational_issues(preview["issues"])

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(METRIC_CONFIRMED, preview["confirmed"])
    m2.metric(METRIC_PACKAGES, preview["packages"])
    m3.metric(METRIC_ITEMS, preview["items"])
    m4.metric(METRIC_ADD, preview["items_add"])
    m5.metric(METRIC_REMOVE, preview["items_remove"])

    if informational:
        st.info(SYNC_INFO_ISSUES)

        for issue in informational[:20]:
            st.write(issue)

    if blocking:
        st.error(SYNC_PLAN_ERRORS)

        for issue in blocking[:30]:
            st.write(issue)

    agree = st.checkbox(
        SYNC_AGREE,
        key="s13_sync_agree",
    )

    button_disabled = (not agree) or bool(blocking)

    if st.button(
        SYNC_BUTTON,
        key="s13_sync_button",
        disabled=button_disabled,
    ):
        ok, messages, stats = _perform_sync()

        if ok:
            st.success(SYNC_SUCCESS)

            if stats:
                st.json(stats)

            st.rerun()
        else:
            if messages and any(str(m).startswith("transferred requirements") for m in messages):
                st.error(SYNC_VALIDATION_ERRORS)
            else:
                st.error(SYNC_EXECUTION_ERROR)

            for message in messages[:30]:
                st.write(message)
