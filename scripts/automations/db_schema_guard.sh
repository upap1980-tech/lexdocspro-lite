#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
DB="lexdocs.db"
if [[ ! -f "$DB" ]]; then
  echo "[FAIL] DB not found: $DB"
  exit 1
fi
python3 - <<'PY'
import sqlite3, sys
conn=sqlite3.connect('lexdocs.db')
cur=conn.cursor()
required={
  'notifications': {'id','user_id','title','message','urgency','is_read','created_at'},
}
ok=True
for t,cols in required.items():
  cur.execute(f"PRAGMA table_info({t})")
  got={r[1] for r in cur.fetchall()}
  miss=cols-got
  if miss:
    ok=False
    print(f"[FAIL] {t} missing columns: {sorted(miss)}")
  else:
    print(f"[OK] {t} schema")
conn.close()
sys.exit(0 if ok else 2)
PY
