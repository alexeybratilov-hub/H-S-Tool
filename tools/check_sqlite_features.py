from __future__ import annotations

import sqlite3


def main() -> None:
    print("SQLITE_VERSION:", sqlite3.sqlite_version)

    conn = sqlite3.connect(":memory:")

    try:
        conn.execute("CREATE VIRTUAL TABLE test_fts USING fts5(x)")
        print("FTS5_AVAILABLE: yes")
    except sqlite3.OperationalError as exc:
        print("FTS5_AVAILABLE: no")
        print("FTS5_ERROR:", exc)

    conn.close()


if __name__ == "__main__":
    main()