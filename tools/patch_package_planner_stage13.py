from pathlib import Path

TARGET = Path("src/ot_agent/ui/package_planner.py")
STATUS = Path("tools/stage13_package_planner_patch_status.txt")
MARKER = "STAGE13_REQUIREMENTS_UI_PATCH_BEGIN"

APPEND_CODE = '''

# STAGE13_REQUIREMENTS_UI_PATCH_BEGIN
_orig_render_stage13 = globals().get("render")

if callable(_orig_render_stage13):
    def render(*args, **kwargs):
        _orig_render_stage13(*args, **kwargs)

        try:
            from ot_agent.ui.stage13_requirements_view import render_stage13_requirements
            render_stage13_requirements()
        except Exception as exc:
            import streamlit as st
            st.error("Stage 13 requirements view error: " + str(exc))
# STAGE13_REQUIREMENTS_UI_PATCH_END
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


def main() -> int:
    if not TARGET.exists():
        return fail("package_planner.py missing")

    text = TARGET.read_text(encoding="utf-8-sig")

    if MARKER in text:
        return done("ALREADY")

    if "def render" not in text and "render =" not in text and "render=" not in text:
        return fail("no global render symbol found")

    if not text.endswith("\n"):
        text += "\n"

    new_text = text + APPEND_CODE

    if MARKER not in new_text:
        return fail("post-patch marker missing")

    TARGET.write_bytes(new_text.encode("utf-8"))
    return done("SUCCESS")


if __name__ == "__main__":
    raise SystemExit(main())
