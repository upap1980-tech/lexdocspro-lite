#!/usr/bin/env python3
"""
P0 Skill: API Contract checker.

Detecta:
- endpoints referenciados por frontend/tests que no existen en backend
- claves de payload enviadas por frontend que backend no consume
- claves esperadas por frontend en la respuesta que no aparecen en jsonify(...)
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass
class BackendRoute:
    path: str
    function: str
    request_keys: Set[str] = field(default_factory=set)
    response_keys: Set[str] = field(default_factory=set)


@dataclass
class FrontEndpointUsage:
    endpoint: str
    sources: Set[str] = field(default_factory=set)
    payload_keys: Set[str] = field(default_factory=set)
    response_keys: Set[str] = field(default_factory=set)


def normalize_endpoint(raw: str) -> str:
    endpoint = raw.split("?", 1)[0].strip()
    endpoint = re.sub(r"\$\{[^}]+\}", "__VAR__", endpoint)
    return endpoint


def route_to_regex(route_path: str) -> re.Pattern[str]:
    pattern = re.escape(route_path)
    pattern = re.sub(r"<[^>]+>", r"[^/]+", pattern)
    return re.compile(rf"^{pattern}$")


def extract_backend_routes(run_path: Path) -> List[BackendRoute]:
    source = run_path.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(source)
    routes: List[BackendRoute] = []

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        paths: List[str] = []
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call):
                continue
            if not isinstance(deco.func, ast.Attribute):
                continue
            if deco.func.attr != "route":
                continue
            if not deco.args:
                continue
            arg0 = deco.args[0]
            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                paths.append(arg0.value)

        if not paths:
            continue

        fn_source = ast.get_source_segment(source, node) or ""
        request_keys = set(
            re.findall(
                r"(?:data|confirmed_data|extracted_data|request\.args|request\.json|request\.form)\.get\(\s*['\"]([^'\"]+)['\"]",
                fn_source,
            )
        )

        response_keys: Set[str] = set()
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            if not isinstance(call.func, ast.Name) or call.func.id != "jsonify":
                continue
            for arg in call.args:
                if isinstance(arg, ast.Dict):
                    for key in arg.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            response_keys.add(key.value)

        for path in paths:
            routes.append(
                BackendRoute(
                    path=path,
                    function=node.name,
                    request_keys=request_keys,
                    response_keys=response_keys,
                )
            )
    return routes


def extract_frontend_usage(files: List[Path]) -> Dict[str, FrontEndpointUsage]:
    usages: Dict[str, FrontEndpointUsage] = {}
    fetch_pattern = re.compile(r"fetch\(\s*([`'\"])(/api[^`'\"]*)\1", re.S)

    for file_path in files:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for match in fetch_pattern.finditer(text):
            raw_endpoint = match.group(2)
            endpoint = normalize_endpoint(raw_endpoint)
            usage = usages.setdefault(endpoint, FrontEndpointUsage(endpoint=endpoint))
            usage.sources.add(str(file_path))

            ctx = text[match.start(): match.start() + 1200]

            body_match = re.search(r"JSON\.stringify\(\s*\{(.*?)\}\s*\)", ctx, re.S)
            if body_match:
                body = body_match.group(1)
                usage.payload_keys.update(
                    re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*:", body)
                )

            usage.response_keys.update(
                re.findall(r"\bdata\.([A-Za-z_][A-Za-z0-9_]*)", ctx)
            )

    return usages


def match_backend_route(endpoint: str, backend_routes: List[BackendRoute]) -> BackendRoute | None:
    for route in backend_routes:
        if endpoint == route.path:
            return route
    for route in backend_routes:
        regex = route_to_regex(route.path)
        if regex.match(endpoint):
            return route
    return None


def build_report(root: Path) -> Dict:
    backend_routes = extract_backend_routes(root / "run.py")
    frontend_files = [
        root / "templates" / "index.html",
        root / "static" / "js" / "app.js",
    ]
    frontend_usage = extract_frontend_usage(frontend_files)

    missing_endpoints = []
    payload_mismatches = []
    response_mismatches = []
    matched = 0

    for endpoint, usage in sorted(frontend_usage.items()):
        backend = match_backend_route(endpoint, backend_routes)
        if not backend:
            missing_endpoints.append(
                {
                    "endpoint": endpoint,
                    "sources": sorted(usage.sources),
                }
            )
            continue

        matched += 1
        unknown_payload = sorted(usage.payload_keys - backend.request_keys)
        if unknown_payload and backend.request_keys:
            payload_mismatches.append(
                {
                    "endpoint": endpoint,
                    "backend_function": backend.function,
                    "frontend_payload_keys": sorted(usage.payload_keys),
                    "backend_request_keys": sorted(backend.request_keys),
                    "unknown_payload_keys": unknown_payload,
                }
            )

        unknown_response = sorted(usage.response_keys - backend.response_keys)
        if unknown_response and backend.response_keys:
            response_mismatches.append(
                {
                    "endpoint": endpoint,
                    "backend_function": backend.function,
                    "frontend_response_keys": sorted(usage.response_keys),
                    "backend_response_keys": sorted(backend.response_keys),
                    "unknown_response_keys": unknown_response,
                }
            )

    status = "PASS"
    if missing_endpoints:
        status = "FAIL"
    elif payload_mismatches or response_mismatches:
        status = "WARN"

    return {
        "skill": "api_contract_skill",
        "status": status,
        "summary": {
            "backend_routes_total": len(backend_routes),
            "frontend_endpoints_total": len(frontend_usage),
            "frontend_endpoints_matched": matched,
            "missing_endpoints": len(missing_endpoints),
            "payload_mismatches": len(payload_mismatches),
            "response_mismatches": len(response_mismatches),
        },
        "missing_endpoints": missing_endpoints,
        "payload_mismatches": payload_mismatches,
        "response_mismatches": response_mismatches,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P0 API Contract Skill")
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Project root",
    )
    parser.add_argument(
        "--out",
        default="reports/p0_api_contract_report.json",
        help="Output JSON file path (relative to root)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(root)

    out_path = root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    s = report["summary"]
    print("API Contract Skill")
    print(f"- status: {report['status']}")
    print(f"- backend routes: {s['backend_routes_total']}")
    print(f"- frontend endpoints: {s['frontend_endpoints_total']}")
    print(f"- matched: {s['frontend_endpoints_matched']}")
    print(f"- missing endpoints: {s['missing_endpoints']}")
    print(f"- payload mismatches: {s['payload_mismatches']}")
    print(f"- response mismatches: {s['response_mismatches']}")
    print(f"- report: {out_path}")

    return 0 if report["status"] in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
