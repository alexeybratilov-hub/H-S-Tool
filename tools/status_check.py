import json
import sqlite3
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"
OLLAMA_URL = "http://127.0.0.1:11434/api/tags"


def hr(title):
    print("")
    print(f"[{title}]")


def check_python():
    hr("PYTHON")
    print(f"version={sys.version.split()[0]}")
    print(f"executable={sys.executable}")

    in_venv = getattr(sys, "base_prefix", None) != sys.prefix
    print(f"venv_active={in_venv}")

    if not in_venv:
        print("warning=Run inside .venv or use start_ot_agent.cmd")


def table_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return bool(row)


def count_table(conn, name):
    if not table_exists(conn, name):
        return None

    try:
        return conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    except sqlite3.Error:
        return None


def check_db():
    hr("DATABASE")
    print(f"path={DB_PATH}")

    if not DB_PATH.exists():
        print("status=MISSING")
        return

    conn = sqlite3.connect(DB_PATH)

    try:
        tables = [
            "companies",
            "departments",
            "positions",
            "employees",
            "staffing_schedules",
            "staffing_schedule_rows",
            "job_descriptions",
            "regulatory_sources",
            "regulatory_chunks",
            "norm_applicability",
            "document_types",
            "baseline_documents",
        ]

        for table in tables:
            count = count_table(conn, table)
            if count is None:
                print(f"{table}=MISSING_TABLE")
            else:
                print(f"{table}={count}")

        if table_exists(conn, "companies"):
            rows = conn.execute(
                "SELECT company_id FROM companies ORDER BY company_id LIMIT 10"
            ).fetchall()

            company_ids = [row[0] for row in rows]
            print("company_ids=" + ",".join(company_ids))

        if table_exists(conn, "baseline_documents"):
            rows = conn.execute(
                """
                SELECT status, COUNT(*)
                FROM baseline_documents
                GROUP BY status
                ORDER BY status
                """
            ).fetchall()

            statuses = ";".join(f"{status}:{count}" for status, count in rows)
            print(f"baseline_statuses={statuses}")

    finally:
        conn.close()


def check_ollama():
    hr("OLLAMA")

    try:
        request = urllib.request.Request(OLLAMA_URL, method="GET")

        with urllib.request.urlopen(request, timeout=2) as response:
            data = json.load(response)

        models = data.get("models", [])
        names = []

        for model in models:
            name = model.get("name")
            if name:
                names.append(name)

        print("status=OK")
        print(f"models_count={len(names)}")

        if names:
            print("models_sample=" + ", ".join(names[:5]))

    except Exception as exc:
        print("status=UNAVAILABLE")
        print(f"detail={type(exc).__name__}")
        print("note=Ollama is optional for non-LLM interface checks")


def main():
    print("OT_LOCAL_AGENT_STATUS_CHECK")
    print("synthetic_only=true")

    check_python()
    check_db()
    check_ollama()

    hr("SUMMARY")
    print("If DATABASE status=MISSING, check 00_SYS/ot_local_agent.sqlite.")
    print("If OLLAMA status=UNAVAILABLE, start or install Ollama only when LLM generation is needed.")



print("\n[STAGE13]")
try:
    import sqlite3
    from pathlib import Path
    _s13_db = Path(__file__).resolve().parents[1] / "00_SYS" / "ot_local_agent.sqlite"
    _s13_conn = sqlite3.connect(str(_s13_db))
    _s13_tables = (
        "harmful_factors",
        "sout_campaigns",
        "sout_workplaces",
        "sout_results",
        "ppe_items",
        "ppe_norms",
        "employee_ppe_cards",
        "ppe_issue_records",
        "ppe_return_records",
        "risk_register",
    )
    for _s13_table in _s13_tables:
        _s13_exists = _s13_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (_s13_table,),
        ).fetchone() is not None

        if _s13_exists:
            _s13_count = _s13_conn.execute("SELECT COUNT(*) FROM " + _s13_table).fetchone()[0]
        else:
            _s13_count = "MISSING"

        print(f"{_s13_table}={_s13_count}")

    _s13_conn.close()
except Exception as _s13_exc:
    print(f"stage13_error={_s13_exc}")



# STAGE13_FINAL_CHECK_BEGIN
def _stage13_final_check():
    import sqlite3
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    db = root / "00_SYS" / "ot_local_agent.sqlite"
    errors = []

    print("\n[STAGE13_FINAL]")

    if not db.exists():
        print("STAGE13_FINAL_CHECK=FAIL")
        print("STAGE13_FINAL_ERROR=db_missing")
        return

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    def table_exists(name):
        return cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone() is not None

    def columns(name):
        return {row[1] for row in cur.execute(f"PRAGMA table_info({name})").fetchall()}

    def count(sql, params=()):
        return int(cur.execute(sql, params).fetchone()[0] or 0)

    has_companies = table_exists("companies")
    if not has_companies:
        errors.append("companies_table_missing")

    # 1. stage13_package_suggestions
    if table_exists("stage13_package_suggestions"):
        cols = columns("stage13_package_suggestions")
        rows = count("SELECT COUNT(*) FROM stage13_package_suggestions")
        print(f"stage13_package_suggestions_rows={rows}")

        if rows <= 0:
            errors.append("stage13_package_suggestions_empty")

        if "status" in cols and "verification_status" in cols:
            bad = count(
                """
                SELECT COUNT(*)
                FROM stage13_package_suggestions
                WHERE status <> 'PRELIMINARY'
                   OR verification_status <> 'REQUIRES_VERIFICATION'
                """
            )
            print(f"stage13_package_suggestions_bad_status_rows={bad}")
            if bad:
                errors.append("stage13_package_suggestions_bad_status")

        if has_companies and "company_id" in cols:
            orphan = count(
                """
                SELECT COUNT(*)
                FROM stage13_package_suggestions
                WHERE company_id IS NULL
                   OR company_id NOT IN (SELECT company_id FROM companies)
                """
            )
            print(f"stage13_package_suggestions_orphan_company_rows={orphan}")
            if orphan:
                errors.append("stage13_package_suggestions_orphan_company")

        if "suggestion_id" in cols:
            dup = count(
                """
                SELECT COUNT(*)
                FROM (
                  SELECT suggestion_id
                  FROM stage13_package_suggestions
                  GROUP BY suggestion_id
                  HAVING COUNT(*) > 1
                )
                """
            )
            print(f"stage13_package_suggestions_duplicate_ids={dup}")
            if dup:
                errors.append("stage13_package_suggestions_duplicate_ids")
    else:
        errors.append("stage13_package_suggestions_table_missing")

    # 2. document_requirements STAGE13_PRELIMINARY
    if table_exists("document_requirements"):
        cols = columns("document_requirements")

        if "source_type" in cols:
            rows = count(
                "SELECT COUNT(*) FROM document_requirements WHERE source_type = ?",
                ("STAGE13_PRELIMINARY",),
            )
            print(f"stage13_requirement_rows={rows}")

            if rows <= 0:
                errors.append("stage13_requirements_empty")

            if "status" in cols:
                for row in cur.execute(
                    """
                    SELECT status, COUNT(*) AS c
                    FROM document_requirements
                    WHERE source_type = ?
                    GROUP BY status
                    ORDER BY status
                    """,
                    ("STAGE13_PRELIMINARY",),
                ).fetchall():
                    print(f"stage13_requirement_status_{row[0]}={row[1]}")

                bad_status = count(
                    """
                    SELECT COUNT(*)
                    FROM document_requirements
                    WHERE source_type = ?
                      AND status NOT IN ('CONFIRMED', 'REJECTED', 'REQUIRES_VERIFICATION')
                    """,
                    ("STAGE13_PRELIMINARY",),
                )
                print(f"stage13_requirement_bad_status_rows={bad_status}")
                if bad_status:
                    errors.append("stage13_requirements_bad_status")

            if has_companies and "company_id" in cols:
                orphan = count(
                    """
                    SELECT COUNT(*)
                    FROM document_requirements
                    WHERE source_type = ?
                      AND (
                        company_id IS NULL
                        OR company_id NOT IN (SELECT company_id FROM companies)
                      )
                    """,
                    ("STAGE13_PRELIMINARY",),
                )
                print(f"stage13_requirement_orphan_company_rows={orphan}")
                if orphan:
                    errors.append("stage13_requirements_orphan_company")

            if "requirement_id" in cols:
                dup = count(
                    """
                    SELECT COUNT(*)
                    FROM (
                      SELECT requirement_id
                      FROM document_requirements
                      WHERE source_type = ?
                      GROUP BY requirement_id
                      HAVING COUNT(*) > 1
                    )
                    """,
                    ("STAGE13_PRELIMINARY",),
                )
                print(f"stage13_requirement_duplicate_ids={dup}")
                if dup:
                    errors.append("stage13_requirements_duplicate_ids")

            if "source_id" in cols:
                dup_source = count(
                    """
                    SELECT COUNT(*)
                    FROM (
                      SELECT company_id, source_id
                      FROM document_requirements
                      WHERE source_type = ?
                      GROUP BY company_id, source_id
                      HAVING COUNT(*) > 1
                    )
                    """,
                    ("STAGE13_PRELIMINARY",),
                )
                print(f"stage13_requirement_duplicate_source_ids={dup_source}")
                if dup_source:
                    errors.append("stage13_requirements_duplicate_source_ids")
        else:
            errors.append("document_requirements_source_type_missing")
    else:
        errors.append("document_requirements_table_missing")

    # 3. technical packages PKG:S13_CONFIRMED:*
    if table_exists("document_packages") and table_exists("package_items"):
        pkg_cols = columns("document_packages")
        item_cols = columns("package_items")

        if "package_id" not in pkg_cols or "company_id" not in pkg_cols:
            errors.append("document_packages_required_columns_missing")
        if "package_id" not in item_cols or "requirement_id" not in item_cols:
            errors.append("package_items_required_columns_missing")

        if (
            "package_id" in pkg_cols
            and "company_id" in pkg_cols
            and "package_id" in item_cols
            and "requirement_id" in item_cols
        ):
            pkg_rows = count(
                "SELECT COUNT(*) FROM document_packages WHERE package_id LIKE ?",
                ("PKG:S13_CONFIRMED:%",),
            )
            print(f"stage13_technical_packages={pkg_rows}")

            if has_companies:
                orphan_pkg = count(
                    """
                    SELECT COUNT(*)
                    FROM document_packages
                    WHERE package_id LIKE ?
                      AND (
                        company_id IS NULL
                        OR company_id NOT IN (SELECT company_id FROM companies)
                      )
                    """,
                    ("PKG:S13_CONFIRMED:%",),
                )
                print(f"stage13_technical_package_orphan_company_rows={orphan_pkg}")
                if orphan_pkg:
                    errors.append("stage13_technical_packages_orphan_company")

            item_rows = count(
                """
                SELECT COUNT(*)
                FROM package_items pi
                JOIN document_packages dp ON dp.package_id = pi.package_id
                WHERE dp.package_id LIKE ?
                """,
                ("PKG:S13_CONFIRMED:%",),
            )
            print(f"stage13_technical_package_items={item_rows}")

            if table_exists("document_requirements"):
                req_cols = columns("document_requirements")

                if {
                    "requirement_id",
                    "company_id",
                    "source_type",
                    "status",
                }.issubset(req_cols):
                    invalid_items = count(
                        """
                        SELECT COUNT(*)
                        FROM package_items pi
                        JOIN document_packages dp ON dp.package_id = pi.package_id
                        LEFT JOIN document_requirements dr ON dr.requirement_id = pi.requirement_id
                        WHERE dp.package_id LIKE ?
                          AND (
                            dr.requirement_id IS NULL
                            OR dr.source_type <> 'STAGE13_PRELIMINARY'
                            OR dr.status <> 'CONFIRMED'
                            OR dr.company_id <> dp.company_id
                          )
                        """,
                        ("PKG:S13_CONFIRMED:%",),
                    )
                    print(f"stage13_technical_package_invalid_items={invalid_items}")
                    if invalid_items:
                        errors.append("stage13_technical_package_invalid_items")

                stale_packages = count(
                    """
                    SELECT COUNT(*)
                    FROM (
                      SELECT dp.package_id
                      FROM document_packages dp
                      LEFT JOIN package_items pi ON pi.package_id = dp.package_id
                      WHERE dp.package_id LIKE ?
                      GROUP BY dp.package_id
                      HAVING COUNT(pi.requirement_id) = 0
                    )
                    """,
                    ("PKG:S13_CONFIRMED:%",),
                )
                print(f"stage13_technical_stale_packages={stale_packages}")
                if stale_packages:
                    errors.append("stage13_technical_stale_packages")

                if table_exists("document_requirements"):
                    req_cols = columns("document_requirements")

                    if {
                        "company_id",
                        "source_type",
                        "status",
                    }.issubset(req_cols):
                        missing_packages = count(
                            """
                            SELECT COUNT(DISTINCT dr.company_id)
                            FROM document_requirements dr
                            WHERE dr.source_type = 'STAGE13_PRELIMINARY'
                              AND dr.status = 'CONFIRMED'
                              AND NOT EXISTS (
                                SELECT 1
                                FROM document_packages dp
                                WHERE dp.package_id = 'PKG:S13_CONFIRMED:' || dr.company_id
                              )
                            """
                        )
                        print(f"stage13_missing_technical_packages={missing_packages}")
                        if missing_packages:
                            errors.append("stage13_missing_technical_packages")
    else:
        errors.append("document_packages_or_package_items_table_missing")

    # 4. controlled marker absence
    if table_exists("draft_versions"):
        dv_cols = columns("draft_versions")
        marker = "STAGE13_MANUAL_CHECK_20261009"
        conditions = []
        params = []

        if "content" in dv_cols:
            conditions.append("content LIKE ?")
            params.append("%" + marker + "%")

        if "author" in dv_cols:
            conditions.append("author = ?")
            params.append(marker)

        if "comment" in dv_cols:
            conditions.append("comment = ?")
            params.append(marker)

        if conditions:
            marker_count = count(
                "SELECT COUNT(*) FROM draft_versions WHERE " + " OR ".join(conditions),
                tuple(params),
            )
            print(f"controlled_stage13_marker_versions={marker_count}")

            if marker_count != 0:
                errors.append("controlled_stage13_marker_present")
        else:
            errors.append("draft_versions_marker_columns_missing")
    else:
        errors.append("draft_versions_table_missing")

    if table_exists("drafts"):
        draft_cols = columns("drafts")

        if "title" in draft_cols:
            titled = count(
                "SELECT COUNT(*) FROM drafts WHERE title LIKE ?",
                ("Stage13 technical draft:%",),
            )
            print(f"stage13_titled_drafts={titled}")

    conn.close()

    if errors:
        print("STAGE13_FINAL_CHECK=FAIL")
        for error in errors:
            print("STAGE13_FINAL_ERROR=" + error)
    else:
        print("STAGE13_FINAL_CHECK=PASS")


if __name__ == "__main__":
    try:
        _stage13_final_check()
    except Exception as exc:
        print("\n[STAGE13_FINAL]")
        print("STAGE13_FINAL_CHECK=ERROR")
        print("STAGE13_FINAL_ERROR=" + str(exc))
# STAGE13_FINAL_CHECK_END
if __name__ == "__main__":
    main()
