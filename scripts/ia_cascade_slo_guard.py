#!/usr/bin/env python3
"""
SLO guard para IA Cascade.

Lee reports/enterprise_modules_audit.json y evalúa:
- success_rate_percent >= min_success_rate
- latency p95 <= max_p95_ms
- failures_5xx <= max_5xx

Genera reports/ia_cascade_slo_guard.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="IA Cascade SLO Guard")
    parser.add_argument("--root", default=".")
    parser.add_argument("--min-success-rate", type=float, default=60.0)
    parser.add_argument("--max-p95-ms", type=float, default=12000.0)
    parser.add_argument("--max-5xx", type=int, default=0)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    audit_path = root / "reports" / "enterprise_modules_audit.json"
    out_path = root / "reports" / "ia_cascade_slo_guard.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not audit_path.exists():
        report = {
            "guard": "ia_cascade_slo",
            "status": "FAIL",
            "error": f"Missing audit report: {audit_path}",
            "timestamp_epoch_ms": int(time.time() * 1000),
        }
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"SLO Guard\n- status: FAIL\n- reason: missing audit report\n- report: {out_path}")
        return 1

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    stress = audit.get("ia_cascade_stress", {})
    success_rate = float(stress.get("success_rate_percent", 0.0))
    p95_ms = float(stress.get("latency_ms", {}).get("p95", 0.0))
    failures_5xx = int(stress.get("failures_5xx", 0))

    checks = {
        "success_rate": {
            "actual": success_rate,
            "threshold": args.min_success_rate,
            "ok": success_rate >= args.min_success_rate,
        },
        "latency_p95_ms": {
            "actual": p95_ms,
            "threshold": args.max_p95_ms,
            "ok": p95_ms <= args.max_p95_ms,
        },
        "failures_5xx": {
            "actual": failures_5xx,
            "threshold": args.max_5xx,
            "ok": failures_5xx <= args.max_5xx,
        },
    }

    status = "PASS" if all(v["ok"] for v in checks.values()) else "ALERT"
    alerts = []
    for name, chk in checks.items():
        if not chk["ok"]:
            alerts.append(
                f"{name} degraded: actual={chk['actual']} threshold={chk['threshold']}"
            )

    report = {
        "guard": "ia_cascade_slo",
        "status": status,
        "checks": checks,
        "alerts": alerts,
        "source_audit_report": str(audit_path),
        "timestamp_epoch_ms": int(time.time() * 1000),
    }
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("SLO Guard")
    print(f"- status: {status}")
    print(f"- success_rate: {success_rate:.2f}% (>= {args.min_success_rate:.2f}%)")
    print(f"- latency_p95_ms: {p95_ms:.2f} (<= {args.max_p95_ms:.2f})")
    print(f"- failures_5xx: {failures_5xx} (<= {args.max_5xx})")
    print(f"- report: {out_path}")
    if alerts:
        print("- alerts:")
        for a in alerts:
            print(f"  - {a}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
