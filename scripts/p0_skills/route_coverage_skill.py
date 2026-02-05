#!/usr/bin/env python3
"""
P0 Skill: Route Coverage map.

Genera mapa endpoint -> test -> estado (OK/FAIL/N/A).
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


@dataclass
class RouteCoverageItem:
    endpoint: str
    methods: List[str]
    status: str
    matched_tests: List[str]
    note: str


def route_to_regex(route_path: str) -> re.Pattern[str]:
    pattern = re.escape(route_path)
    pattern = re.sub(r"<[^>]+>", r"[^/]+", pattern)
    return re.compile(rf"^{pattern}$")


def parse_routes(run_py: Path) -> Dict[str, List[str]]:
    text = run_py.read_text(encoding="utf-8", errors="ignore")
    route_pattern = re.compile(
        r"@app\.route\(\s*['\"]([^'\"]+)['\"](?:,\s*methods\s*=\s*\[([^\]]*)\])?",
        re.S,
    )
    routes: Dict[str, List[str]] = {}
    for m in route_pattern.finditer(text):
        path = m.group(1)
        methods_raw = m.group(2)
        methods = ["GET"]
        if methods_raw:
            methods = [x.strip().strip("'\"") for x in methods_raw.split(",") if x.strip()]
        routes[path] = methods
    return routes


def parse_test_endpoints(test_files: List[Path]) -> Dict[str, List[str]]:
    endpoint_hits: Dict[str, List[str]] = {}
    endpoint_re = re.compile(r"['\"](/api/[^'\"\s]*)['\"]")
    for test_file in test_files:
        text = test_file.read_text(encoding="utf-8", errors="ignore")
        found = sorted(set(endpoint_re.findall(text)))
        for ep in found:
            endpoint_hits.setdefault(ep, []).append(str(test_file))
    return endpoint_hits


def build_report(root: Path) -> Dict:
    routes = parse_routes(root / "run.py")
    test_files = sorted((root / "tests").glob("test_*.py"))
    test_endpoints = parse_test_endpoints(test_files)

    items: List[RouteCoverageItem] = []
    for endpoint, methods in sorted(routes.items()):
        if not endpoint.startswith("/api/"):
            items.append(
                RouteCoverageItem(
                    endpoint=endpoint,
                    methods=methods,
                    status="N/A",
                    matched_tests=[],
                    note="Ruta no API",
                )
            )
            continue

        matched_test_files = set()
        endpoint_regex = route_to_regex(endpoint)
        for test_ep, files in test_endpoints.items():
            normalized = test_ep.split("?", 1)[0]
            if normalized == endpoint or endpoint_regex.match(normalized):
                matched_test_files.update(files)

        if matched_test_files:
            items.append(
                RouteCoverageItem(
                    endpoint=endpoint,
                    methods=methods,
                    status="OK",
                    matched_tests=sorted(matched_test_files),
                    note="Cubierto por test(s)",
                )
            )
        else:
            items.append(
                RouteCoverageItem(
                    endpoint=endpoint,
                    methods=methods,
                    status="FAIL",
                    matched_tests=[],
                    note="Sin cobertura de tests detectada",
                )
            )

    api_items = [i for i in items if i.endpoint.startswith("/api/")]
    ok_items = [i for i in api_items if i.status == "OK"]
    fail_items = [i for i in api_items if i.status == "FAIL"]
    na_items = [i for i in items if i.status == "N/A"]
    coverage_pct = round((len(ok_items) / len(api_items) * 100), 2) if api_items else 0.0

    return {
        "skill": "route_coverage_skill",
        "status": "PASS",
        "summary": {
            "total_routes": len(items),
            "api_routes": len(api_items),
            "ok_routes": len(ok_items),
            "fail_routes": len(fail_items),
            "na_routes": len(na_items),
            "coverage_percent": coverage_pct,
            "test_files_scanned": len(test_files),
        },
        "items": [asdict(i) for i in items],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P0 Route Coverage Skill")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Project root",
    )
    parser.add_argument(
        "--out",
        default="reports/p0_route_coverage_report.json",
        help="Output JSON report path (relative to root)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(root)

    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    s = report["summary"]
    print("Route Coverage Skill")
    print(f"- routes total: {s['total_routes']}")
    print(f"- api routes: {s['api_routes']}")
    print(f"- OK: {s['ok_routes']}")
    print(f"- FAIL: {s['fail_routes']}")
    print(f"- N/A: {s['na_routes']}")
    print(f"- coverage: {s['coverage_percent']}%")
    print(f"- report: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
