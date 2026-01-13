import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from demo_app.server import DemoServer
from framework.config import load_env_config
from framework.data_factory import DataFactory
from framework.http_client import HttpClient
from framework.logger import init_logger
from framework.allure_utils import attach_file


@pytest.fixture(scope="session", autouse=True)
def _init_logging():
    init_logger()
    return


@pytest.fixture(scope="session")
def env_config():
    return load_env_config()


@pytest.fixture(scope="session")
def base_url(env_config):
    base_url = os.getenv("BASE_URL") or env_config.base_url
    if base_url:
        yield base_url
        return

    if env_config.name != "local":
        raise RuntimeError("BASE_URL is required for non-local environments")

    html_path = ROOT / "demo_app" / "web" / "index.html"
    html = html_path.read_text(encoding="utf-8")
    server = DemoServer(index_html=html)
    server.start()
    os.environ["BASE_URL"] = server.base_url
    yield server.base_url
    server.stop()


@pytest.fixture(scope="session")
def api_client(base_url, env_config):
    return HttpClient(
        base_url=base_url,
        timeout_sec=env_config.timeout_sec,
        verify_ssl=env_config.verify_ssl,
    )


@pytest.fixture(scope="session")
def data_factory():
    return DataFactory()


@pytest.fixture(scope="session")
def artifact_dir():
    path = Path(os.getenv("ARTIFACT_DIR", ROOT / "reports" / "artifacts"))
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def cleanup_tasks():
    tasks = []
    yield tasks
    logger = init_logger("cleanup")
    for task in reversed(tasks):
        try:
            task()
        except Exception as exc:
            logger.warning("Cleanup task failed: %s", exc)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture
def ui_page(base_url, artifact_dir, request):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    headless = os.getenv("HEADLESS", "1") != "0"
    browser_name = os.getenv("BROWSER", "chromium")
    trace_enabled = os.getenv("PW_TRACE", "0") == "1"

    with sync_playwright() as p:
        browser_type = getattr(p, browser_name)
        browser = browser_type.launch(headless=headless)
        context = browser.new_context()
        if trace_enabled:
            context.tracing.start(screenshots=True, snapshots=True, sources=False)
        page = context.new_page()
        yield page
        failed = getattr(request.node, "rep_call", None) and request.node.rep_call.failed
        if failed:
            screenshot = artifact_dir / f"{request.node.name}.png"
            try:
                page.screenshot(path=str(screenshot), full_page=True)
            except Exception:
                screenshot = None
            if screenshot and screenshot.exists():
                attach_file("ui_failure_screenshot", screenshot, mime="image/png")
        if trace_enabled:
            trace_path = artifact_dir / f"{request.node.name}.zip"
            if failed:
                context.tracing.stop(path=str(trace_path))
                if trace_path.exists():
                    attach_file("playwright_trace", trace_path, mime="application/zip")
            else:
                context.tracing.stop()
        context.close()
        browser.close()
