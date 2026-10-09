import ast
import sys
from pathlib import Path

TARGET = Path("tools/status_check.py")
STATUS = Path("tools/stage13_status_patch_status.txt")
MARKER = "[STAGE13]"

BLOCK = r'''
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


def find_insert_line(tree: ast.AST, lines: list[str]) -> int:
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

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return fail(f"status_check.py syntax before patch: {exc}")

    lines = text.splitlines(keepends=True)

    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    insert_idx = find_insert_line(tree, lines)

    block_text = BLOCK.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    block_lines = block_text.splitlines(keepends=True)

    if block_lines and not block_lines[-1].endswith("\n"):
        block_lines[-1] += "\n"

    insert_block = ["\n"] + block_lines + ["\n"]
    lines[insert_idx:insert_idx] = insert_block

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
