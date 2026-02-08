#!/usr/bin/env python3
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run

app = run.app
client = app.test_client()

fixtures_dir = Path("tests/fixtures")
pdf_path = fixtures_dir / "lexnet_notification.pdf"
xml_path = fixtures_dir / "lexnet_notification.xml"

report = {"ok": True, "checks": []}

def record(name, ok, status, note=""):
    report["checks"].append({"name": name, "ok": ok, "status": status, "note": note})
    if not ok:
        report["ok"] = False

# Auth flow
email = "p0@test.local"
password = "test12345"

res = client.post("/api/auth/register", json={"email": email, "password": password, "rol": "ADMIN"})
record("auth.register", res.status_code < 500, res.status_code, res.get_data(as_text=True)[:200])

res = client.post("/api/auth/login", json={"email": email, "password": password})
token = None
if res.status_code == 200:
    payload = res.get_json() or {}
    token = payload.get("access_token")
record("auth.login", res.status_code < 500, res.status_code, res.get_data(as_text=True)[:200])

headers = {"Authorization": f"Bearer {token}"} if token else {}

# Health check
res = client.get("/api/health")
record("health", res.status_code == 200, res.status_code, res.get_data(as_text=True)[:200])

# OCR (local)
res = client.post("/api/ocr", json={"filename": "missing.pdf"})
record("ocr.local", res.status_code < 500, res.status_code, res.get_data(as_text=True)[:200])

# OCR upload
if pdf_path.exists():
    data = {"file": (io.BytesIO(pdf_path.read_bytes()), "fixture.pdf")}
    res = client.post("/api/ocr/upload", data=data, content_type="multipart/form-data")
    record("ocr.upload", res.status_code < 500, res.status_code, res.get_data(as_text=True)[:200])

# DocumentProcessing smart-analyze
if pdf_path.exists():
    data = {"file": (io.BytesIO(pdf_path.read_bytes()), "fixture.pdf")}
    res = client.post("/api/document/smart-analyze", data=data, content_type="multipart/form-data", headers=headers)
    record("doc.smart_analyze", res.status_code < 500, res.status_code, res.get_data(as_text=True)[:200])

# LexNET upload + list + read + urgent count
if xml_path.exists():
    data = {"file": (io.BytesIO(xml_path.read_bytes()), "lexnet.xml")}
    res = client.post("/api/lexnet/upload-notification", data=data, content_type="multipart/form-data", headers=headers)
    record("lexnet.upload", res.status_code < 500, res.status_code, res.get_data(as_text=True)[:200])

res = client.get("/api/lexnet/notifications?limit=5", headers=headers)
record("lexnet.list", res.status_code < 500, res.status_code, res.get_data(as_text=True)[:200])

if res.status_code == 200:
    data = res.get_json() or {}
    if data.get("notifications"):
        nid = data["notifications"][0].get("id")
        if nid:
            res2 = client.patch(f"/api/lexnet/notifications/{nid}/read", headers=headers)
            record("lexnet.read", res2.status_code < 500, res2.status_code, res2.get_data(as_text=True)[:200])

res = client.get("/api/lexnet/urgent-count", headers=headers)
record("lexnet.urgent_count", res.status_code < 500, res.status_code, res.get_data(as_text=True)[:200])

# IA cascade quick
res = client.post("/api/ia-cascade/query", json={"prompt": "ping"})
record("ia.cascade", res.status_code < 500, res.status_code, res.get_data(as_text=True)[:200])

# Autoprocesador status
res = client.get("/api/autoprocessor/status")
record("autoprocesor.status", res.status_code < 500, res.status_code, res.get_data(as_text=True)[:200])

Path("reports").mkdir(exist_ok=True)
out = Path("reports/p0_runtime_validation.json")
out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
print(out)
