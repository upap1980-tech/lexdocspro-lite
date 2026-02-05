#!/usr/bin/env python3
"""
Auditoría profunda de módulos críticos:
- Dashboard
- AutoProcessor
- IA Cascade (incluye pruebas de estrés de prompt/max_tokens)

Genera:
- reports/enterprise_modules_audit.json
"""

from __future__ import annotations

import json
import statistics
import time
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run


@dataclass
class AuditResult:
    module: str
    endpoint: str
    method: str
    status_code: int
    ok: bool
    elapsed_ms: float
    detail: str
    app_success: Optional[bool] = None
    provider_used: Optional[str] = None


class EnterpriseAuditor:
    def __init__(self):
        self.client = run.app.test_client()
        self.results: List[AuditResult] = []

    def _record(
        self,
        module: str,
        endpoint: str,
        method: str,
        response,
        elapsed_ms: float,
        detail: str = "",
        app_success: Optional[bool] = None,
        provider_used: Optional[str] = None,
    ):
        ok = response.status_code < 500
        self.results.append(
            AuditResult(
                module=module,
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                ok=ok,
                elapsed_ms=elapsed_ms,
                detail=detail,
                app_success=app_success,
                provider_used=provider_used,
            )
        )

    def _req(self, module: str, method: str, endpoint: str, json_body: Optional[Dict] = None):
        t0 = time.perf_counter()
        if method == "GET":
            resp = self.client.get(endpoint)
        elif method == "POST":
            resp = self.client.post(endpoint, json=json_body or {})
        elif method == "PATCH":
            resp = self.client.patch(endpoint, json=json_body or {})
        else:
            raise ValueError(f"Método no soportado: {method}")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        payload = {}
        try:
            payload = resp.get_json(silent=True) or {}
        except Exception:
            payload = {}
        detail = ""
        if isinstance(payload, dict):
            if payload.get("error"):
                detail = str(payload.get("error"))[:200]
            elif "success" in payload:
                detail = f"success={payload.get('success')}"
        self._record(
            module,
            endpoint,
            method,
            resp,
            elapsed_ms,
            detail,
            app_success=payload.get("success") if isinstance(payload, dict) else None,
            provider_used=payload.get("provider_used") or payload.get("provider"),
        )
        return resp

    def audit_dashboard(self):
        endpoints = [
            ("GET", "/api/dashboard/stats"),
            ("GET", "/api/dashboard/stats-detailed"),
            ("GET", "/api/dashboard/drill-down/by-date/05%20Feb?limit=20"),
        ]
        for method, endpoint in endpoints:
            self._req("dashboard", method, endpoint)

    def audit_autoprocess(self):
        endpoints = [
            ("GET", "/api/autoprocessor/status", None),
            ("POST", "/api/autoprocessor/scan", {}),
            ("GET", "/api/autoprocessor/log?limit=20", None),
            ("POST", "/api/autoprocessor/reset", {}),
        ]
        for method, endpoint, payload in endpoints:
            self._req("autoprocessor", method, endpoint, payload)

    def audit_ia_cascade_baseline(self):
        endpoints = [
            ("GET", "/api/ia-cascade/health", None),
            ("GET", "/api/ia-cascade/stats-public", None),
            ("GET", "/api/ia-cascade/providers-public", None),
            ("GET", "/api/ia-cascade/stats", None),
        ]
        for method, endpoint, payload in endpoints:
            self._req("ia_cascade", method, endpoint, payload)

    def audit_ia_cascade_stress(self):
        # Forzar "IA al máximo": prompt largo, max_tokens alto, temp alta.
        long_prompt = (
            "Analiza exhaustivamente y estructura riesgos legales, estrategia procesal y plan de acción. "
            * 300
        )[:14000]
        stress_payload = {
            "prompt": long_prompt,
            "provider": "cascade",
            "temperature": 1.0,
            "max_tokens": 12000,  # servicio sanitiza a límite seguro
        }
        # Repeticiones para medir estabilidad/latencia.
        samples_ms = []
        failures = 0
        for _ in range(5):
            resp = self._req("ia_cascade_stress", "POST", "/api/ia-cascade/test", stress_payload)
            samples_ms.append(self.results[-1].elapsed_ms)
            if resp.status_code >= 500:
                failures += 1
        stress_items = [r for r in self.results if r.module == "ia_cascade_stress" and r.endpoint == "/api/ia-cascade/test"]
        app_success_count = sum(1 for r in stress_items if r.app_success is True)
        provider_usage: Dict[str, int] = {}
        for r in stress_items:
            if r.provider_used:
                provider_usage[r.provider_used] = provider_usage.get(r.provider_used, 0) + 1

        # Test endpoint legacy query con prompt largo
        legacy_payload = {"prompt": long_prompt}
        self._req("ia_cascade_stress", "POST", "/api/ia-cascade/query", legacy_payload)

        return {
            "iterations": 5,
            "failures_5xx": failures,
            "success_count": app_success_count,
            "success_rate_percent": (app_success_count / 5.0) * 100.0,
            "provider_usage": provider_usage,
            "latency_ms": {
                "min": min(samples_ms) if samples_ms else 0.0,
                "max": max(samples_ms) if samples_ms else 0.0,
                "avg": statistics.mean(samples_ms) if samples_ms else 0.0,
                "p50": statistics.median(samples_ms) if samples_ms else 0.0,
                "p95": (
                    sorted(samples_ms)[max(0, min(len(samples_ms) - 1, int(round(0.95 * (len(samples_ms) - 1)))))]
                    if samples_ms
                    else 0.0
                ),
            },
        }

    def run(self):
        self.audit_dashboard()
        self.audit_autoprocess()
        self.audit_ia_cascade_baseline()
        stress = self.audit_ia_cascade_stress()

        ok = [r for r in self.results if r.ok]
        fail = [r for r in self.results if not r.ok]
        by_module: Dict[str, Dict[str, int]] = {}
        for r in self.results:
            mod = by_module.setdefault(r.module, {"ok": 0, "fail": 0})
            if r.ok:
                mod["ok"] += 1
            else:
                mod["fail"] += 1

        report = {
            "audit": "enterprise_modules",
            "summary": {
                "total_checks": len(self.results),
                "ok": len(ok),
                "fail": len(fail),
                "status": "PASS" if not fail else "WARN",
            },
            "by_module": by_module,
            "ia_cascade_stress": stress,
            "results": [asdict(r) for r in self.results],
            "timestamp_epoch_ms": int(time.time() * 1000),
        }
        return report


def main() -> int:
    root = ROOT
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "enterprise_modules_audit.json"

    auditor = EnterpriseAuditor()
    report = auditor.run()
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    s = report["summary"]
    print("Enterprise Modules Audit")
    print(f"- status: {s['status']}")
    print(f"- checks: {s['total_checks']}")
    print(f"- ok: {s['ok']}")
    print(f"- fail: {s['fail']}")
    stress = report["ia_cascade_stress"]
    print(
        f"- ia_cascade_stress avg(ms): {stress['latency_ms']['avg']:.2f} "
        f"| max(ms): {stress['latency_ms']['max']:.2f} | 5xx: {stress['failures_5xx']}"
    )
    print(f"- report: {out_path}")
    return 0 if s["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
