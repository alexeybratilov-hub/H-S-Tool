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

if __name__ == "__main__":
    main()
