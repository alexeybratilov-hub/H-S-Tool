import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ot_agent.drafts_db import (
    activate_rule,
    add_correction,
    add_version,
    create_draft,
    get_connection,
    init_draft_schema,
    list_corrections,
)

DB_PATH = ROOT / "00_SYS" / "ot_local_agent.sqlite"


def main() -> None:
    init_draft_schema(DB_PATH)

    conn = get_connection(DB_PATH)

    try:
        company_id = "LLC_TEST_ALPHA"

        draft_id = create_draft(
            conn,
            company_id=company_id,
            title="Stage 11 test draft",
            document_type="INSTRUCTION",
            requirement_id=None,
            initial_content="Line one\n",
        )

        add_version(
            conn,
            draft_id=draft_id,
            content="Line one edited\n",
            author="tester",
            comment="edit 1",
        )

        add_version(
            conn,
            draft_id=draft_id,
            content="Line one edited\nLine two added\n",
            author="tester",
            comment="edit 2",
        )

        add_correction(
            conn,
            draft_id=draft_id,
            from_version=1,
            to_version=2,
            category="wording",
            old_snippet="Line one",
            new_snippet="Line one edited",
            comment="Test correction",
            proposed_rule="Use short sentences.",
        )

        corrections = list_corrections(conn, draft_id)

        if corrections:
            activate_rule(conn, corrections[-1]["correction_id"])

        conn.commit()

        print("drafts=", conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0])
        print("versions=", conn.execute("SELECT COUNT(*) FROM draft_versions").fetchone()[0])
        print("diffs=", conn.execute("SELECT COUNT(*) FROM version_diffs").fetchone()[0])
        print("corrections=", conn.execute("SELECT COUNT(*) FROM corrections").fetchone()[0])
        print("active_rules=", conn.execute("SELECT COUNT(*) FROM active_rules").fetchone()[0])
        print("TEST_DRAFT_ID=", draft_id)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
