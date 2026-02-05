#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run  # noqa: E402


@dataclass
class Row:
    phase: str
    module: str
    endpoint: str
    methods: str
    status: str
    owner: str
    file: str
    action: str


MODULE_RULES: List[Tuple[str, List[str], str]] = [
    ("Dashboard", ["/api/dashboard/"], "P0"),
    ("AutoProcessor v2", ["/api/autoprocessor/"], "P0"),
    ("IA Cascade", ["/api/ia-cascade/"], "P0"),
    ("Documentos", ["/api/document/", "/api/documents/"], "P1"),
    ("LexNET", ["/api/lexnet", "/api/lexnet/"], "P1"),
    ("OCR/PDF/Files", ["/api/ocr", "/api/ocr/", "/api/pdf/", "/api/files"], "P1"),
    ("iCloud", ["/api/icloud/"], "P1"),
    ("AutoProcesador legacy", ["/api/autoprocesador/", "/api/autoprocesos/", "/api/watchdog-status"], "P1"),
    ("Alertas", ["/api/alerts/"], "P2"),
    ("Firma digital", ["/api/signature/", "/api/firma/"], "P2"),
    ("Banking", ["/api/banking/"], "P2"),
    ("Usuarios", ["/api/usuarios/"], "P2"),
    ("Analytics/Expedientes", ["/api/analytics/", "/api/expedientes/"], "P2"),
    ("Config/Deploy", ["/api/config/", "/api/deploy/"], "P2"),
    ("Business skills", ["/api/business/"], "P2"),
    ("IA general/Chat", ["/api/chat", "/api/ai/", "/api/ia/", "/api/agent/feedback"], "P2"),
]


def _normalize(endpoint: str) -> str:
    endpoint = endpoint.split("?")[0]
    endpoint = re.sub(r"<[^>]+>", "{var}", endpoint)
    endpoint = re.sub(r"\$\{[^}]*\}", "{var}", endpoint)
    endpoint = re.sub(r"\$\{[^/]*", "{var}", endpoint)
    endpoint = endpoint.replace("}", "")
    endpoint = endpoint.replace("{var{var", "{var}")
    return endpoint.rstrip("/")


def _extract_frontend_api_patterns(path: Path) -> List[str]:
    s = path.read_text(encoding="utf-8", errors="ignore")
    return sorted(set(re.findall(r"/api/[A-Za-z0-9_\-./<>:?=&{}$]+", s)))


def _classify_module(endpoint: str) -> Tuple[str, str]:
    for module, prefixes, phase in MODULE_RULES:
        for p in prefixes:
            if endpoint == p or endpoint.startswith(p):
                return module, phase
    return "Otros", "P2"


def main() -> int:
    backend_rules = []
    for r in sorted(run.app.url_map.iter_rules(), key=lambda x: x.rule):
        if not r.rule.startswith("/api/"):
            continue
        methods = sorted([m for m in r.methods if m not in {"HEAD", "OPTIONS"}])
        backend_rules.append((r.rule, methods))

    index_patterns = {_normalize(x) for x in _extract_frontend_api_patterns(ROOT / "templates" / "index.html")}
    app_patterns = {_normalize(x) for x in _extract_frontend_api_patterns(ROOT / "static" / "js" / "app.js")}

    rows: List[Row] = []
    summary: Dict[str, Dict[str, int]] = {}

    for endpoint, methods in backend_rules:
        module, phase = _classify_module(endpoint)
        n = _normalize(endpoint)
        if n in index_patterns:
            status = "OK"
            owner = "QA+Frontend"
            file = "templates/index.html"
            action = "Mantener cobertura visual activa y añadir test funcional."
        elif n in app_patterns:
            status = "PARCIAL"
            owner = "Frontend"
            file = "templates/index.html"
            action = "Conectar endpoint en UI activa (hoy solo referenciado en static/js/app.js)."
        else:
            status = "SIN CORRESPONDENCIA"
            owner = "Frontend+Backend"
            file = "templates/index.html, run.py"
            action = "Crear/activar vista y contrato de consumo para este endpoint."

        rows.append(
            Row(
                phase=phase,
                module=module,
                endpoint=endpoint,
                methods=",".join(methods),
                status=status,
                owner=owner,
                file=file,
                action=action,
            )
        )
        summary.setdefault(phase, {"OK": 0, "PARCIAL": 0, "SIN CORRESPONDENCIA": 0})
        summary[phase][status] += 1

    rows.sort(key=lambda x: (x.phase, x.module, x.endpoint))

    docs_dir = ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    md_path = docs_dir / "CHECKLIST_CIERRE_BACKEND_FRONTEND.md"
    json_path = docs_dir / "CHECKLIST_CIERRE_BACKEND_FRONTEND.json"

    lines = [
        "# Checklist Ejecutable Backend → Frontend",
        "",
        "Estados: `OK`, `PARCIAL`, `SIN CORRESPONDENCIA`.",
        "",
        "## Resumen",
        "",
        "| Fase | OK | PARCIAL | SIN CORRESPONDENCIA |",
        "|---|---:|---:|---:|",
    ]
    for phase in ("P0", "P1", "P2"):
        s = summary.get(phase, {"OK": 0, "PARCIAL": 0, "SIN CORRESPONDENCIA": 0})
        lines.append(f"| {phase} | {s['OK']} | {s['PARCIAL']} | {s['SIN CORRESPONDENCIA']} |")

    lines.extend(
        [
            "",
            "## Endpoint Por Endpoint",
            "",
            "| Fase | Módulo | Endpoint | Método | Estado | Owner | Archivo | Acción |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for r in rows:
        lines.append(
            f"| {r.phase} | {r.module} | `{r.endpoint}` | `{r.methods}` | {r.status} | {r.owner} | `{r.file}` | {r.action} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "summary": summary,
                "rows": [r.__dict__ for r in rows],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Checklist generado:\n- {md_path}\n- {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
