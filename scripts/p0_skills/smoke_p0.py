#!/usr/bin/env python3
"""
Smoke P0:
- run.py arranca sin import errors
- UI principal sin JS fatal
- endpoints criticos devuelven 2xx/4xx (no 500)
- ejecuta Skills P0 y genera reportes
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def run_import_check(root: Path) -> Tuple[bool, str]:
    code = "import run; print('OK')"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    ok = result.returncode == 0
    msg = result.stdout.strip() if ok else (result.stderr.strip() or result.stdout.strip())
    return ok, msg


def run_skill_script(root: Path, relative_script: str, out_file: str) -> Dict:
    script_path = root / relative_script
    cmd = [sys.executable, str(script_path), "--root", str(root), "--out", out_file]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    report_path = root / out_file
    report = {}
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    return {
        "script": relative_script,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "report": report,
    }


def run_endpoint_checks(root: Path) -> Dict:
    # Import directo para usar Flask test_client sin red
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    run_module = importlib.import_module("run")
    app = run_module.app
    client = app.test_client()

    checks = [
        ("GET", "/api/files", None),
        ("GET", "/api/ai/providers", None),
        ("GET", "/api/documents/templates", None),
        ("GET", "/api/document/types", None),
        ("GET", "/api/autoprocessor/status", None),
        ("GET", "/api/autoprocessor/log", None),
        ("GET", "/api/ia-cascade/stats-public", None),
        ("GET", "/api/ia-cascade/providers-public", None),
        ("POST", "/api/ocr", {"filename": "archivo_inexistente.pdf"}),
        ("POST", "/api/ocr/upload", None),  # debe responder 4xx controlado
        ("POST", "/api/document/propose-save", {}),
        ("POST", "/api/document/confirm-save", {}),
    ]

    results = []
    all_ok = True

    for method, path, payload in checks:
        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            if payload is None:
                response = client.post(path)
            else:
                response = client.post(path, json=payload)
        else:
            raise ValueError(f"Metodo no soportado: {method}")

        status = response.status_code
        ok = status < 500
        if not ok:
            all_ok = False

        results.append(
            {
                "method": method,
                "path": path,
                "status_code": status,
                "ok_non_500": ok,
            }
        )

    return {"status": "PASS" if all_ok else "FAIL", "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke P0")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Project root",
    )
    parser.add_argument(
        "--out",
        default="reports/p0_smoke_report.json",
        help="Output report path (relative to root)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()

    import_ok, import_msg = run_import_check(root)

    frontend_skill = run_skill_script(
        root,
        "scripts/p0_skills/frontend_integrity_skill.py",
        "reports/p0_frontend_integrity_report.json",
    )
    api_contract_skill = run_skill_script(
        root,
        "scripts/p0_skills/api_contract_skill.py",
        "reports/p0_api_contract_report.json",
    )
    route_coverage_skill = run_skill_script(
        root,
        "scripts/p0_skills/route_coverage_skill.py",
        "reports/p0_route_coverage_report.json",
    )

    endpoint_checks = run_endpoint_checks(root)

    # Gating P0: solo criterios de salida solicitados
    gating_ok = (
        import_ok
        and frontend_skill["report"].get("status") == "PASS"
        and endpoint_checks["status"] == "PASS"
    )

    smoke_report = {
        "skill": "p0_smoke",
        "status": "PASS" if gating_ok else "FAIL",
        "criteria": {
            "run_import_ok": import_ok,
            "ui_no_js_fatal": frontend_skill["report"].get("status") == "PASS",
            "critical_endpoints_non_500": endpoint_checks["status"] == "PASS",
        },
        "details": {
            "run_import_message": import_msg,
            "frontend_integrity_skill": frontend_skill,
            "api_contract_skill": api_contract_skill,
            "route_coverage_skill": route_coverage_skill,
            "endpoint_checks": endpoint_checks,
        },
    }

    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(smoke_report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Smoke P0")
    print(f"- status: {smoke_report['status']}")
    print(f"- run import: {'OK' if import_ok else 'FAIL'}")
    print(f"- frontend integrity: {frontend_skill['report'].get('status', 'N/A')}")
    print(f"- endpoints non-500: {endpoint_checks['status']}")
    print(f"- report: {out_path}")

    return 0 if smoke_report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
