#!/usr/bin/env python3
"""
P0 Skill: Frontend Integrity checker.

Detecta:
- scripts truncados/HTML incompleto
- errores de sintaxis JS (assets cargados por la UI principal)
- duplicados de funciones y asignaciones globales (warning)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List


def _run_node_check(js_code: str, label: str) -> str | None:
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
            tmp.write(js_code)
            tmp_path = tmp.name
        result = subprocess.run(
            ["node", "--check", tmp_path],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return f"{label}: {result.stderr.strip() or result.stdout.strip()}"
        return None
    except FileNotFoundError:
        return "node_not_found: no se pudo validar sintaxis JS con node --check"


def check_html_main_ui(index_html: Path) -> Dict:
    findings = []
    text = index_html.read_text(encoding="utf-8", errors="ignore")

    script_open = len(re.findall(r"<script\b", text, re.I))
    script_close = len(re.findall(r"</script>", text, re.I))
    if script_open != script_close:
        findings.append(
            {
                "severity": "fatal",
                "code": "script_tag_imbalance",
                "message": f"Script tags desbalanceados: open={script_open}, close={script_close}",
            }
        )

    if "</body>" not in text.lower():
        findings.append(
            {"severity": "fatal", "code": "missing_body_close", "message": "Falta </body>"}
        )
    if "</html>" not in text.lower():
        findings.append(
            {"severity": "fatal", "code": "missing_html_close", "message": "Falta </html>"}
        )

    scripts = re.findall(r"<script[^>]*>(.*?)</script>", text, flags=re.S | re.I)
    for i, script in enumerate(scripts, start=1):
        if not script.strip():
            continue
        syntax_error = _run_node_check(script, f"inline_script_{i}")
        if syntax_error:
            findings.append(
                {
                    "severity": "fatal",
                    "code": "inline_js_syntax_error",
                    "message": syntax_error,
                }
            )

    local_srcs = re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", text, flags=re.I)
    for src in local_srcs:
        if src.startswith("http://") or src.startswith("https://") or src.startswith("//"):
            continue
        findings.append(
            {
                "severity": "warning",
                "code": "local_script_reference",
                "message": f"Referencia local detectada: {src}",
            }
        )

    return {"file": str(index_html), "findings": findings}


def check_js_duplicates(js_path: Path) -> Dict:
    findings = []
    text = js_path.read_text(encoding="utf-8", errors="ignore")

    fn_names = re.findall(r"(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", text)
    counts = {}
    for name in fn_names:
        counts[name] = counts.get(name, 0) + 1
    duplicated_functions = sorted([name for name, qty in counts.items() if qty > 1])
    if duplicated_functions:
        findings.append(
            {
                "severity": "warning",
                "code": "duplicated_functions",
                "message": f"Funciones duplicadas ({len(duplicated_functions)}): {', '.join(duplicated_functions[:15])}",
            }
        )

    globals_names = re.findall(r"window\.([A-Za-z_$][A-Za-z0-9_$]*)\s*=", text)
    gcounts = {}
    for name in globals_names:
        gcounts[name] = gcounts.get(name, 0) + 1
    duplicated_globals = sorted([name for name, qty in gcounts.items() if qty > 1])
    if duplicated_globals:
        findings.append(
            {
                "severity": "warning",
                "code": "duplicated_window_assignments",
                "message": f"window.* duplicados ({len(duplicated_globals)}): {', '.join(duplicated_globals[:15])}",
            }
        )

    suspicious_lines = []
    for n, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped in {");", "async"} or stripped.startswith(");"):
            suspicious_lines.append(str(n))
    if suspicious_lines:
        findings.append(
            {
                "severity": "warning",
                "code": "suspicious_truncation_patterns",
                "message": f"Lineas sospechosas: {', '.join(suspicious_lines[:20])}",
            }
        )

    return {"file": str(js_path), "findings": findings}


def build_report(root: Path) -> Dict:
    index_html = root / "templates" / "index.html"
    js_files = sorted((root / "static" / "js").glob("*.js"))

    ui_check = check_html_main_ui(index_html)
    js_checks = [check_js_duplicates(path) for path in js_files]

    all_findings = ui_check["findings"] + [f for c in js_checks for f in c["findings"]]
    fatal = [f for f in all_findings if f["severity"] == "fatal"]
    warnings = [f for f in all_findings if f["severity"] == "warning"]

    status = "PASS" if not fatal else "FAIL"
    return {
        "skill": "frontend_integrity_skill",
        "status": status,
        "summary": {
            "fatal_findings": len(fatal),
            "warning_findings": len(warnings),
            "files_checked": 1 + len(js_files),
        },
        "ui_main_check": ui_check,
        "js_duplicate_checks": js_checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P0 Frontend Integrity Skill")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Project root",
    )
    parser.add_argument(
        "--out",
        default="reports/p0_frontend_integrity_report.json",
        help="Output JSON report path (relative to root)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(root)

    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = report["summary"]
    print("Frontend Integrity Skill")
    print(f"- status: {report['status']}")
    print(f"- files checked: {summary['files_checked']}")
    print(f"- fatal findings: {summary['fatal_findings']}")
    print(f"- warning findings: {summary['warning_findings']}")
    print(f"- report: {out_path}")

    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
