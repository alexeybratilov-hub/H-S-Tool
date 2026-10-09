import re
import shutil
import sys
from pathlib import Path

APP = Path("app.py")
BAK = Path("app.py.stage13.bak")
STATUS = Path("tools/stage13_patch_status.txt")

MARKER = "render_sout_ppe_risk"
IMPORT_TEXT = "from ot_agent.ui.sout_ppe_risk import render as render_sout_ppe_risk"
IMPORT_LINE = IMPORT_TEXT + "\n"

NEW_LABEL = "\u0421\u041e\u0423\u0422 / \u0421\u0418\u0417 / \u0420\u0438\u0441\u043a\u0438"
OLD_LABEL = "\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c \u0441\u0440\u043e\u043a\u043e\u0432"
SETTINGS_LABEL = "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438"

CONDITION_RE = re.compile(
    r'''^(\s*)(if|elif)\s+([A-Za-z_][A-Za-z0-9_.]*)\s*==\s*(['"])(.*?)\4\s*:\s*(#.*)?$'''
)


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


def get_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def find_condition_for_label(lines, label):
    for i, line in enumerate(lines):
        m = CONDITION_RE.match(line.rstrip("\n"))
        if m and m.group(5) == label:
            return i, m.group(1), m.group(2), m.group(3)
    return None


def find_periodic_render(lines):
    render_re = re.compile(
        r"periodic_control\s*\.\s*render\s*\(|render_periodic_control\s*\("
    )

    for i, line in enumerate(lines):
        if render_re.search(line):
            for j in range(i, max(-1, i - 80), -1):
                m = CONDITION_RE.match(lines[j].rstrip("\n"))
                if m and (m.group(5) == OLD_LABEL or "periodic" in lines[j].lower()):
                    return j, i, m.group(1), m.group(2), m.group(3)

            for j in range(i, max(-1, i - 80), -1):
                m = CONDITION_RE.match(lines[j].rstrip("\n"))
                if m:
                    return j, i, m.group(1), m.group(2), m.group(3)

    return None


def block_end(lines, start_after, cond_indent):
    idx = start_after

    while idx < len(lines):
        line = lines[idx]

        if not line.strip():
            idx += 1
            continue

        if get_indent(line) > cond_indent:
            idx += 1
            continue

        break

    return idx


def insert_branch(lines, end_idx, indent, var):
    lines[end_idx:end_idx] = [
        f"{indent}elif {var} == '{NEW_LABEL}':\n",
        f"{indent}    render_sout_ppe_risk()\n",
    ]


def add_import(lines):
    text = "".join(lines)

    if IMPORT_TEXT in text:
        return lines

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("import streamlit as st") or stripped.startswith("from streamlit"):
            lines.insert(i + 1, IMPORT_LINE)
            return lines

    idx = 0
    while idx < len(lines) and (lines[idx].startswith("#") or not lines[idx].strip()):
        idx += 1

    lines.insert(idx, IMPORT_LINE)
    return lines


def patch_dict_or_list(lines):
    for i, line in enumerate(lines):
        if SETTINGS_LABEL not in line:
            continue

        stripped = line.strip()
        indent = " " * get_indent(line)

        if stripped.endswith(","):
            new_line = f"{indent}'{NEW_LABEL}',\n"
        elif ":" in stripped:
            new_line = f"{indent}'{NEW_LABEL}': render_sout_ppe_risk,\n"
        else:
            continue

        lines.insert(i, new_line)
        return True

    return False


def main() -> int:
    if not APP.exists():
        return fail("app.py missing")

    text = APP.read_text(encoding="utf-8-sig")

    if MARKER in text and NEW_LABEL in text and IMPORT_TEXT in text:
        return done("ALREADY")

    shutil.copy2(APP, BAK)

    try:
        lines = text.splitlines(keepends=True)

        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"

        periodic = find_periodic_render(lines)

        if periodic:
            cond_idx, render_idx, indent, _kw, var = periodic
            end = block_end(lines, render_idx + 1, get_indent(lines[cond_idx]))
            insert_branch(lines, end, indent, var)
        else:
            settings = find_condition_for_label(lines, SETTINGS_LABEL)

            if settings:
                cond_idx, indent, _kw, var = settings
                end = block_end(lines, cond_idx + 1, get_indent(lines[cond_idx]))
                insert_branch(lines, end, indent, var)
            elif patch_dict_or_list(lines):
                pass
            else:
                return fail("no supported app.py menu pattern found")

        lines = add_import(lines)
        new_text = "".join(lines)

        if MARKER not in new_text:
            return fail("post-patch marker missing")

        if NEW_LABEL not in new_text:
            return fail("post-patch label missing")

        if IMPORT_TEXT not in new_text:
            return fail("post-patch import missing")

        APP.write_bytes(new_text.encode("utf-8"))
        return done("SUCCESS")

    except Exception as exc:
        if BAK.exists():
            shutil.copy2(BAK, APP)
        return fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
