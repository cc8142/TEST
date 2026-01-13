# Automation Test Engineer Portfolio (5 Years)

![Automation Architecture](docs/automation-architecture.svg)

## Why This Repo
- Production-style layering: client -> service -> page objects with pytest fixtures
- Environment governance: `config/environments.json` + env overrides, local demo server for offline runs
- Stability controls: retry policy, flaky reruns, suite markers, parallel options
- Observability: JUnit XML + rich HTML summary + optional Allure results
- CI-ready: Jenkinsfile and GitLab CI templates

## Tech Stack
- Python, Pytest, Requests, Playwright
- Allure, JUnit XML, custom HTML summary
- Jenkins, GitLab CI, data factory, quality metrics

## Clone & Setup
- Clone: `git clone https://github.com/cc8142/TEST.git`
- Create venv: `python -m venv venv`
- Activate (Windows): `venv\Scripts\activate`
- Activate (macOS/Linux): `source venv/bin/activate`

## Quick Start (offline)
- Install base deps: `pip install -r requirements.txt`
- Smoke (fast gate): `python tests/run_all.py --suite smoke --env local`
- API regression: `python tests/run_all.py --suite api --env local`
- UI contract (no browser): `python tests/run_all.py --suite ui_contract --env local`
- Browser UI (Playwright): `pip install -r requirements-ui.txt` then `python -m playwright install`
- Run browser UI: `python tests/run_all.py --suite ui --env local --headed`
- Playwright trace on failure: `PW_TRACE=1`
- Parallel + reruns: `python tests/run_all.py --suite api --workers 2 --reruns 2`
- Generate Allure HTML: `python tests/run_all.py --suite api --allure-report`
- Clean reports: `scripts/clean_reports.ps1` / `scripts/clean_reports.sh`
- Windows helper: `scripts/run_demo.ps1`
- Bash helper: `scripts/run_demo.sh`

Outputs: `reports/summary.html`, `reports/summary.json`, `reports/junit.xml`, `reports/artifacts/` (summary includes reruns/flaky counts and failure breakdown).

## Allure Report (optional)
- Generate: `allure generate reports/allure-results -o reports/allure-report --clean`
- Open: `allure open reports/allure-report`

## Python Support
- Tested with Python 3.10 / 3.11 / 3.12

## Environment Variables
- See `.env.example` for the full list
- Key controls: `ENV`, `BASE_URL`, `HTTP_TIMEOUT`, `VERIFY_SSL`, `BROWSER`, `HEADLESS`, `PW_TRACE`, `REDACT_KEYS`, `TEST_USERNAME`, `TEST_PASSWORD`, `TEST_TENANT_PREFIX`

## Local Demo Server
- For `ENV=local`, the demo server auto-starts and binds to a free port.
- The resolved base URL is included in `reports/summary.json` and Allure metadata.

## Failure Triage Example
- Open `reports/summary.html` to locate the failing test.
- In Allure, open the test to see steps plus request/response attachments.
- If it is a UI failure, check `reports/artifacts/` for screenshots.

## Engineering Guardrails
- Install dev tools: `pip install -r requirements-dev.txt`
- Enable pre-commit: `pre-commit install`
- Security scan: `bandit -r framework tests`

## Reproducible Installs
- Full stack pin (includes UI deps): `pip install -r requirements.lock`

## Suite Map
- `smoke`: PR gating, fast checks
- `api`: API regression
- `ui`: Playwright UI regression (browser)
- `ui_contract`: HTML contract checks (no browser)
- `e2e`: end-to-end flows

## Stability Controls
- Prefer per-test reruns: `@pytest.mark.flaky(reruns=2, reruns_delay=1)`
- Use `--reruns` only for temporary global retries
- HTTP retries apply to idempotent methods and transient status codes

## Repository Map
- `framework/`: config, HTTP client, retry policy, data factory, assertions
- `tests/api/services/`: API service layer
- `tests/ui/pages/`: page objects
- `config/`: environment profiles
- `docs/`: strategy, framework, CI, metrics, data/env
- `scripts/`: run helpers

## How to Read
1. `docs/strategy.md` for methodology
2. `docs/framework.md` for architecture and layer design
3. `docs/ci.md` and `docs/metrics.md` for execution and results
4. `docs/case-study.md` for project stories

## Notes
- Playwright is optional; browser tests auto-skip if not installed. Use `ui_contract` for no-browser checks.
- Local demo server is used by default; set `BASE_URL` for remote environments.
- The runner disables pytest auto plugin loading by default; set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=0` to re-enable.
