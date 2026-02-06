#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import re
import sys
import time
import os
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TEMPLATE = ROOT / "templates" / "index.html"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


ALLOWED_STATUS = {200, 201, 202, 204, 400, 401, 403, 404, 405}


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def section_slices(html: str) -> List[Tuple[str, str]]:
    sec_re = re.compile(r'<section\s+id="([^"]+)"[^>]*>', re.I)
    matches = list(sec_re.finditer(html))
    out = []
    for i, m in enumerate(matches):
        sid = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        out.append((sid, html[start:end]))
    return out


def extract_buttons_and_fields(section_html: str):
    btn_re = re.compile(r'<button[^>]*onclick="([^"]+)"[^>]*>(.*?)</button>', re.I | re.S)
    field_re = re.compile(r'<(input|select|textarea)[^>]*\sid="([^"]+)"[^>]*>', re.I)

    buttons = []
    for m in btn_re.finditer(section_html):
        onclick = m.group(1).strip()
        fn = onclick.split("(")[0].strip()
        label = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        buttons.append({"onclick": onclick, "function": fn, "label": label})

    fields = []
    for m in field_re.finditer(section_html):
        fields.append({"type": m.group(1).lower(), "id": m.group(2)})

    return buttons, fields


def extract_script(html: str) -> str:
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S | re.I)
    return "\n".join(scripts)


def parse_functions(js: str) -> Dict[str, str]:
    fn_re = re.compile(r"(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\([^)]*\)\s*\{", re.S)
    fns = {}
    for m in fn_re.finditer(js):
        name = m.group(1)
        i = m.end() - 1
        depth = 0
        j = i
        while j < len(js):
            ch = js[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    fns[name] = js[m.start():j + 1]
                    break
            j += 1
    return fns


def extract_calls(fn_body: str):
    calls = []

    # apiJson('/api/x', { method: 'POST' ... })
    for m in re.finditer(r"apiJson\(\s*([`\"'])(.+?)\1\s*(?:,\s*\{(.*?)\})?\s*\)", fn_body, re.S):
        url = m.group(2)
        opts = m.group(3) or ""
        mm = re.search(r"method\s*:\s*['\"](GET|POST|PUT|PATCH|DELETE)['\"]", opts, re.I)
        method = (mm.group(1).upper() if mm else "GET")
        calls.append({"url": url, "method": method, "kind": "apiJson"})

    # fetch('/api/x', {...})
    for m in re.finditer(r"fetch\(\s*([`\"'])(.+?)\1\s*(?:,\s*\{(.*?)\})?\s*\)", fn_body, re.S):
        url = m.group(2)
        opts = m.group(3) or ""
        mm = re.search(r"method\s*:\s*['\"](GET|POST|PUT|PATCH|DELETE)['\"]", opts, re.I)
        method = (mm.group(1).upper() if mm else "GET")
        calls.append({"url": url, "method": method, "kind": "fetch"})

    return calls


def normalize_path(url: str) -> str:
    if "?" in url:
        url = url.split("?", 1)[0]
    # keep template strings in report, but for testing replace likely placeholders
    url = re.sub(r"\$\{[^}]+\}", "1", url)
    return url


def payload_for(path: str, method: str):
    # returns kwargs for flask test_client method
    if method in {"GET", "DELETE"}:
        return {}

    # multipart uploads
    if path in {"/api/ocr/upload", "/api/lexnet/upload-notification", "/api/document/smart-analyze"}:
        file_name = "fixture.pdf"
        content = b"%PDF-1.4\n% test fixture\n"
        if "lexnet" in path:
            file_name = "fixture.xml"
            content = b"<notification><title>Test</title></notification>"
        return {
            "data": {
                "file": (io.BytesIO(content), file_name)
            },
            "content_type": "multipart/form-data"
        }

    # json payloads
    data = {}
    if path == "/api/chat":
        data = {
            "prompt": "Analiza y resume este caso. " * 400,
            "provider": "ollama",
            "mode": "standard",
            "context": ""
        }
    elif path == "/api/ia/consultar":
        data = {"prompt": "Consulta legal extensa. " * 500, "provider": "ollama"}
    elif path == "/api/ia/agent-task":
        data = {"task": "Generar estrategia procesal detallada para expediente demo"}
    elif path == "/api/ia-cascade/query":
        data = {"prompt": "Redacta informe legal completo. " * 600}
    elif path == "/api/lexnet/analyze":
        data = {
            "textos": {"principal": "Notificacion judicial de prueba con plazo de 5 dias."},
            "provider": "ollama",
            "archivos": ["fixture.txt"],
            "nombre": "Prueba Forense"
        }
    elif path == "/api/lexnet/analizar-plazo":
        data = {"dias": 20}
    elif path == "/api/autoprocesos/toggle":
        data = {"action": "status"}
    elif path == "/api/autoprocesador/rechazar/1":
        data = {"motivo": "Test forense"}
    elif path == "/api/autoprocesador/aprobar/1":
        data = {"usuario_modifico": False}
    elif path == "/api/signature/sign":
        data = {"doc_id": 1, "certificate": "demo-cert.p12", "passphrase": "demo"}
    elif path == "/api/alerts/config":
        data = {"email": "audit@example.com"}
    elif path == "/api/alerts/test-email":
        data = {"email": "audit@example.com"}
    elif path == "/api/config/save":
        data = {"ollama_model": "lexdocs-legal-pro", "ia_fallback": True}
    elif path == "/api/agent/feedback":
        data = {"expediente_id": 1, "contenido": "feedback test", "score": 1}
    elif path == "/api/business/strategy":
        data = {
            "jurisdiction": "ES_GENERAL",
            "doc_type": "escrito_tramite",
            "query": "plazo reposicion",
            "fecha_notificacion": "2026-02-05",
            "plazo_dias": 5
        }
    else:
        data = {}

    return {"json": data}


def resolve_dynamic(path: str) -> str:
    # common client-side templating placeholders
    path = path.replace("${id}", "1")
    path = path.replace("${n.id}", "1")
    path = path.replace("${notificationId}", "1")
    path = path.replace("${docId}", "1")
    # generic leftover
    path = re.sub(r"\$\{[^}]+\}", "1", path)
    return path


def route_exists(path: str, method: str, url_map) -> bool:
    for rule in url_map.iter_rules():
        if method not in rule.methods:
            continue
        # normalize dynamic flask rules
        rp = rule.rule
        rp_norm = re.sub(r"<[^>]+>", "1", rp)
        if rp_norm == path:
            return True
    return False


def call_endpoint(client, path: str, method: str):
    fn = getattr(client, method.lower())
    kwargs = payload_for(path, method)
    t0 = time.time()
    resp = fn(path, **kwargs)
    dt = int((time.time() - t0) * 1000)
    body = resp.get_data(as_text=True)[:800]
    ok = resp.status_code in ALLOWED_STATUS
    return {
        "status_code": resp.status_code,
        "ok": ok,
        "latency_ms": dt,
        "body_excerpt": body
    }


def run_audit():
    os.environ.setdefault("LEXDOCS_DISABLE_WATCHDOG", "1")
    # Force fast-fail for IA calls during audit
    os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:1")
    os.environ.setdefault("OLLAMA_URL", "http://127.0.0.1:1")
    os.environ.setdefault("GROQ_API_KEY", "")
    os.environ.setdefault("PERPLEXITY_API_KEY", "")
    os.environ.setdefault("OPENAI_API_KEY", "")
    os.environ.setdefault("GEMINI_API_KEY", "")
    os.environ.setdefault("DEEPSEEK_API_KEY", "")
    os.environ.setdefault("ANTHROPIC_API_KEY", "")
    html = read_text(TEMPLATE)
    js = extract_script(html)
    funcs = parse_functions(js)
    native_handlers = {"window.open", "alert", "console.log"}

    sections = section_slices(html)
    modules = []
    endpoint_tests = {}

    # app import late to keep parsing independent
    from run import app  # type: ignore

    client = app.test_client()

    for sid, section_html in sections:
        buttons, fields = extract_buttons_and_fields(section_html)

        mod = {
            "module": sid,
            "buttons_total": len(buttons),
            "fields_total": len(fields),
            "buttons": [],
            "fields": fields,
        }

        for b in buttons:
            fn = b["function"]
            fn_body = funcs.get(fn, "")
            calls = extract_calls(fn_body) if fn_body else []

            call_results = []
            for c in calls:
                p = normalize_path(resolve_dynamic(c["url"]))
                m = c["method"].upper()
                exists = route_exists(p, m, app.url_map)
                test = {
                    "path": p,
                    "method": m,
                    "route_exists": exists,
                }
                if exists:
                    key = f"{m} {p}"
                    if key not in endpoint_tests:
                        try:
                            endpoint_tests[key] = call_endpoint(client, p, m)
                        except Exception as e:
                            endpoint_tests[key] = {
                                "status_code": 0,
                                "ok": False,
                                "latency_ms": 0,
                                "body_excerpt": f"EXCEPTION: {e}",
                            }
                    test["result"] = endpoint_tests[key]
                else:
                    test["result"] = {
                        "status_code": 0,
                        "ok": False,
                        "latency_ms": 0,
                        "body_excerpt": "ROUTE_NOT_FOUND"
                    }
                call_results.append(test)

            mod["buttons"].append({
                "label": b["label"],
                "onclick": b["onclick"],
                "function": fn,
                "function_found": bool(fn_body) or (fn in native_handlers),
                "calls": call_results,
            })

        # module status
        total_calls = 0
        fail_calls = 0
        missing_fn = 0
        for b in mod["buttons"]:
            if not b["function_found"]:
                missing_fn += 1
            for c in b["calls"]:
                total_calls += 1
                if not c["result"]["ok"]:
                    fail_calls += 1
        mod["status"] = "OK" if (missing_fn == 0 and fail_calls == 0) else ("PARCIAL" if (total_calls > 0 or mod["buttons_total"] > 0) else "N/A")
        mod["summary"] = {
            "missing_functions": missing_fn,
            "endpoint_calls": total_calls,
            "endpoint_failures": fail_calls,
        }

        modules.append(mod)

    # IA stress test (forense)
    ai_cases = [
        ("POST", "/api/chat", {"prompt": "A" * 12000, "provider": "ollama", "mode": "standard", "context": ""}),
        ("POST", "/api/ia/consultar", {"prompt": "B" * 15000, "provider": "ollama"}),
        ("POST", "/api/ia-cascade/query", {"prompt": "C" * 18000}),
    ]

    ai_results = []
    for method, path, payload in ai_cases:
        latencies = []
        codes = []
        failures_5xx = 0
        for _ in range(8):
            t0 = time.time()
            r = client.post(path, json=payload)
            dt = int((time.time() - t0) * 1000)
            latencies.append(dt)
            codes.append(r.status_code)
            if r.status_code >= 500:
                failures_5xx += 1
        ai_results.append({
            "endpoint": path,
            "runs": len(codes),
            "codes": codes,
            "avg_latency_ms": int(sum(latencies) / len(latencies)),
            "p95_latency_ms": sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)],
            "error_rate_5xx": round(failures_5xx / len(codes), 3),
            "status": "PASS" if failures_5xx == 0 else "FAIL"
        })

    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "modules": modules,
        "ai_stress": ai_results,
    }

    json_path = REPORTS / "forensic_module_audit.json"
    md_path = REPORTS / "forensic_module_audit.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append("# Auditoría Forense Módulo por Módulo")
    lines.append("")
    lines.append(f"Generado: {report['generated_at']}")
    lines.append("")

    ok = sum(1 for m in modules if m["status"] == "OK")
    parcial = sum(1 for m in modules if m["status"] == "PARCIAL")
    na = sum(1 for m in modules if m["status"] == "N/A")
    lines.append(f"Resumen módulos: OK={ok} | PARCIAL={parcial} | N/A={na}")
    lines.append("")

    for m in modules:
        lines.append(f"## {m['module']} [{m['status']}]")
        lines.append(f"- Botones: {m['buttons_total']}")
        lines.append(f"- Campos: {m['fields_total']}")
        lines.append(f"- Funciones faltantes: {m['summary']['missing_functions']}")
        lines.append(f"- Llamadas endpoint: {m['summary']['endpoint_calls']}")
        lines.append(f"- Fallos endpoint: {m['summary']['endpoint_failures']}")
        lines.append("")

    lines.append("## Stress IA")
    for r in ai_results:
        lines.append(f"- {r['endpoint']}: {r['status']} | runs={r['runs']} | avg={r['avg_latency_ms']}ms | p95={r['p95_latency_ms']}ms | 5xx={r['error_rate_5xx']}")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(json_path))
    print(str(md_path))
    # Hard-exit to avoid lingering background threads (watchdog/observers)
    os._exit(0)


if __name__ == "__main__":
    run_audit()
    native_handlers = {"window.open", "alert", "console.log"}
