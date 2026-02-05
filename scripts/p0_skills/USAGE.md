# P0 Skills (Stabilization)

## Included Skills

- `api_contract_skill.py`
  - Detects endpoint/payload/response mismatches between backend and frontend.
- `frontend_integrity_skill.py`
  - Detects JS syntax issues, truncated HTML/script blocks, and duplicate JS declarations.
- `route_coverage_skill.py`
  - Builds endpoint -> tests -> status map (`OK` / `FAIL` / `N/A`).
- `smoke_p0.py`
  - Runs P0 exit criteria checks and embeds skill reports.

## Run All

```bash
./scripts/p0_skills/run_p0.sh
```

## Reports

All reports are written to:

- `reports/p0_api_contract_report.json`
- `reports/p0_frontend_integrity_report.json`
- `reports/p0_route_coverage_report.json`
- `reports/p0_smoke_report.json`
