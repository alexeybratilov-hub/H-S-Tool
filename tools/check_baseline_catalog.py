import sqlite3, sys
from pathlib import Path
DB_PATH = Path(__file__).resolve().parents[1] / "00_SYS" / "ot_local_agent.sqlite"
conn = sqlite3.connect(DB_PATH)
t = conn.execute("SELECT COUNT(*) FROM document_types").fetchone()[0]
d = conn.execute("SELECT COUNT(*) FROM baseline_documents").fetchone()[0]
print(f"types: {t} | docs: {d}")
conn.close()
