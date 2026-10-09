import ast
import sys
from pathlib import Path

TARGET = Path("tools/status_check.py")
STATUS = Path("tools/stage14_electrical_patch_status.txt")
MARKER = "# STAGE14_ELECTRICAL_CHECK_BEGIN"

BLOCK = r'''
# STAGE14_ELECTRICAL_CHECK_BEGIN
def _stage14_electrical_check():
    import sys
    from pathlib import Path

    print("\n[ELECTRICAL]")

    root = Path(__file__).resolve().parents[1]
    src_dir = root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    try:
        from ot_agent.electrical_safety_db import get_connection, summary, validate_integrity
    except Exception as exc:
        print("ELECTRICAL_CHECK=ERROR")
        print("ELECTRICAL_ERROR=import:" + str(exc))
        return

    conn = None
    try:
        conn = get_connection()
        snap = summary(conn)

        for table, value in sorted(snap.items()):
            print(f"{table}={value}")

        errors = validate_integrity(conn)

        if errors:
            print("ELECTRICAL_CHECK=FAIL")
            for error in errors[:50]:
                print("ELECTRICAL_ERROR=" + error)
        else:
            print("ELECTRICAL_CHECK=PASS")
    except Exception as exc:
        print("ELECTRICAL_CHECK=ERROR")
        print("ELECTRICAL_ERROR=" + str(exc))
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    try:
        _stage14_electrical_check()
    except Exception as exc:
        print("\n[ELECTRICAL]")
        print("ELECTRICAL_CHECK=ERROR")
        print("ELECTRICAL_ERROR=" + str(exc))
# STAGE14_ELECTRICAL_CHECK_END
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
