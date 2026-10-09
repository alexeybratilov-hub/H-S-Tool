import ast
import sys
from pathlib import Path

TARGET = Path("tools/status_check.py")
STATUS = Path("tools/stage13_final_patch_status.txt")
MARKER = "# STAGE13_FINAL_CHECK_BEGIN"

BLOCK = r'''

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
'''


def write_status(value: str) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(value, encoding="ascii")


def fail(message: str) -> int:
    write_status("FAILED")
    print(f"PATCH_STATUS=FAILED ERROR={message}")
    return 1


def done(value: str) -> int:
    write_status(value)
    print(f"PATCH_STATUS={value}")
    return 0


def find_main_guard(lines: list[str]) -> int:
    text = "".join(lines)

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise RuntimeError(f"status_check.py syntax before patch: {exc}") from exc

    for node in tree.body:
        if isinstance(node, ast.If):
            try:
                dump = ast.dump(node.test)
            except Exception:
                dump = ""

            if "__name__" in dump:
                return max(0, node.lineno - 1)

    return len(lines)


def main() -> int:
    if not TARGET.exists():
        return fail("status_check.py missing")

    text = TARGET.read_text(encoding="utf-8-sig")

    if MARKER in text:
        return done("ALREADY")

    lines = text.splitlines(keepends=True)

    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    try:
        insert_idx = find_main_guard(lines)
    except Exception as exc:
        return fail(str(exc))

    block_text = BLOCK.replace("\r\n", "\n").replace("\r", "\n")

    if not block_text.endswith("\n"):
        block_text += "\n"

    block_lines = block_text.splitlines(keepends=True)
    lines[insert_idx:insert_idx] = block_lines

    new_text = "".join(lines)

    if MARKER not in new_text:
        return fail("post-patch marker missing")

    try:
        compile(new_text, str(TARGET), "exec")
    except SyntaxError as exc:
        return fail(f"post-patch syntax: {exc}")

    TARGET.write_bytes(new_text.encode("utf-8"))
    return done("SUCCESS")


if __name__ == "__main__":
    raise SystemExit(main())
