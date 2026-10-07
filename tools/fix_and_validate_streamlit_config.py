from __future__ import annotations

import tomllib
from datetime import datetime
from pathlib import Path

PROJECT_CONFIG = Path.cwd() / ".streamlit" / "config.toml"
USER_CONFIG = Path.home() / ".streamlit" / "config.toml"

PROJECT_CONTENT = """[server]
address = "127.0.0.1"
port = 8501
headless = false

[browser]
gatherUsageStats = false
"""

USER_CONTENT = """[browser]
gatherUsageStats = false
"""


def backup(path: Path) -> None:
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = path.with_name(path.name + f".bak_{stamp}")
        target.write_bytes(path.read_bytes())
        print(f"Backup created: {target}")


def write_no_bom(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path)
    path.write_text(content, encoding="utf-8")
    print(f"Config written without BOM: {path}")


def validate(path: Path) -> bool:
    print(f"\nValidating: {path}")

    if not path.exists():
        print("Status: missing")
        return False

    raw = path.read_bytes()
    print(f"Size: {len(raw)} bytes")
    print(f"UTF-8 BOM present: {raw.startswith(b'\xef\xbb\xbf')}")
    print(f"First 80 bytes repr: {raw[:80]!r}")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"Decode error: {exc}")
        return False

    try:
        parsed = tomllib.loads(text)
    except Exception as exc:
        print(f"TOML parse error: {exc}")
        return False

    print("TOML parse: OK")
    print(f"Top-level keys: {sorted(parsed.keys())}")

    browser = parsed.get("browser", {})
    server = parsed.get("server", {})

    if isinstance(browser, dict):
        print(f"browser.gatherUsageStats = {browser.get('gatherUsageStats')}")

    if isinstance(server, dict):
        print(f"server.address = {server.get('address')}")
        print(f"server.port = {server.get('port')}")

    return True


def main() -> None:
    print("Repairing Streamlit configs...")

    write_no_bom(PROJECT_CONFIG, PROJECT_CONTENT)
    write_no_bom(USER_CONFIG, USER_CONTENT)

    ok_project = validate(PROJECT_CONFIG)
    ok_user = validate(USER_CONFIG)

    print("\nResult:")
    print(f"Project config OK: {ok_project}")
    print(f"User config OK: {ok_user}")

    if ok_project and ok_user:
        print("Configs are valid. You can restart Streamlit.")
    else:
        print("Some config is still invalid. Send the output above.")


if __name__ == "__main__":
    main()