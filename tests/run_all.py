import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.reporting import build_summary, write_reports

SUITE_MARKERS = {
    "api": "api",
    "ui": "ui",
    "ui_contract": "ui_contract",
    "smoke": "smoke",
    "e2e": "e2e",
}


def _plugin_available(module_name):
    return importlib.util.find_spec(module_name) is not None


def main():
    parser = argparse.ArgumentParser(description="Run automation suites with reports.")
    parser.add_argument(
        "--suite",
        choices=["all", "api", "ui", "ui_contract", "smoke", "e2e"],
        default="all",
    )
    parser.add_argument("--env", default=os.getenv("ENV", "local"))
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", ""))
    parser.add_argument("--report-dir", default=str(ROOT / "reports"))
    parser.add_argument("--allure-dir", default="")
    parser.add_argument("--allure-report", action="store_true", help="Generate Allure HTML report")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--reruns", type=int, default=0)
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default=os.getenv("BROWSER", "chromium"),
    )
    parser.add_argument("--headed", action="store_true", help="Run browsers with UI")
    args = parser.parse_args()

    os.environ["ENV"] = args.env
    if args.base_url:
        os.environ["BASE_URL"] = args.base_url
    os.environ["BROWSER"] = args.browser
    os.environ["HEADLESS"] = "0" if args.headed else "1"
    os.environ.setdefault("ALLURE_ATTACH", "1")
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    junit_path = report_dir / "junit.xml"
    os.environ["ARTIFACT_DIR"] = str(report_dir / "artifacts")

    start = datetime.utcnow()
    run_id = start.strftime("%Y%m%d-%H%M%S")

    pytest_args = [
        str(ROOT / "tests"),
        "--junitxml",
        str(junit_path),
        "--strict-markers",
        "-ra",
    ]
    plugins = []

    def _register_plugin(module_name, plugin_name=None):
        if _plugin_available(module_name):
            name = plugin_name or module_name
            if name not in plugins:
                plugins.append(name)
            return True
        return False

    if args.suite != "all":
        pytest_args += ["-m", SUITE_MARKERS[args.suite]]

    if args.workers and args.workers > 1:
        if _register_plugin("xdist") or _register_plugin("pytest_xdist", "pytest_xdist"):
            pytest_args += ["-n", str(args.workers)]
        else:
            print("xdist not installed; running without parallel workers.")

    if args.reruns and args.reruns > 0:
        if _register_plugin("pytest_rerunfailures"):
            pytest_args += ["--reruns", str(args.reruns)]
        else:
            print("pytest-rerunfailures not installed; reruns disabled.")

    allure_dir = args.allure_dir or str(report_dir / "allure-results")
    if _register_plugin("allure_pytest"):
        os.environ["ALLURE_RESULTS_DIR"] = allure_dir
        pytest_args += ["--alluredir", allure_dir, "--clean-alluredir"]

    if plugins:
        plugin_args = []
        for plugin in plugins:
            plugin_args += ["-p", plugin]
        pytest_args = plugin_args + pytest_args

    import pytest

    exit_code = pytest.main(pytest_args)

    end = datetime.utcnow()
    context = {
        "run_id": run_id,
        "env": args.env,
        "suite": args.suite,
        "base_url": os.getenv("BASE_URL", ""),
        "start_time": start.isoformat() + "Z",
        "end_time": end.isoformat() + "Z",
        "duration_sec": round((end - start).total_seconds(), 2),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pytest": pytest.__version__,
        "command": " ".join(sys.argv),
        "workers": args.workers,
        "reruns": args.reruns,
        "browser": args.browser,
        "headed": args.headed,
    }

    summary = build_summary(junit_path, context)
    write_reports(summary, report_dir)
    _write_allure_meta(allure_dir, context)
    if args.allure_report or os.getenv("ALLURE_REPORT", "0") == "1":
        _generate_allure_report(allure_dir, report_dir)
    print(f"Report generated at {report_dir / 'summary.html'}")
    return exit_code


def _write_allure_meta(allure_dir, context):
    if not _plugin_available("allure_pytest"):
        return
    path = Path(allure_dir)
    path.mkdir(parents=True, exist_ok=True)

    env_lines = [
        f"ENV={context.get('env', '')}",
        f"SUITE={context.get('suite', '')}",
        f"BASE_URL={context.get('base_url', '')}",
        f"PYTHON={context.get('python', '')}",
        f"PLATFORM={context.get('platform', '')}",
    ]
    (path / "environment.properties").write_text("\n".join(env_lines), encoding="utf-8")

    executor = {
        "name": "Local Runner",
        "type": "local",
        "buildName": context.get("run_id", ""),
        "buildUrl": "",
        "reportName": "Automation Report",
        "reportUrl": "",
    }
    (path / "executor.json").write_text(json.dumps(executor, indent=2), encoding="utf-8")

    categories = [
        {
            "name": "Product Defects",
            "matchedStatuses": ["failed"],
            "messageRegex": "AssertionError|expected|assert",
        },
        {
            "name": "Test Infrastructure",
            "matchedStatuses": ["broken"],
            "messageRegex": "ConnectionError|Timeout|Playwright",
        },
    ]
    (path / "categories.json").write_text(json.dumps(categories, indent=2), encoding="utf-8")


def _generate_allure_report(allure_dir, report_dir):
    if not _plugin_available("allure_pytest"):
        return
    allure_path = shutil.which("allure")
    if not allure_path:
        print("Allure CLI not found; skipping report generation.")
        return
    out_dir = Path(report_dir) / "allure-report"
    if allure_path.lower().endswith(".ps1"):
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            allure_path,
            "generate",
            str(allure_dir),
            "-o",
            str(out_dir),
            "--clean",
        ]
    else:
        cmd = [allure_path, "generate", str(allure_dir), "-o", str(out_dir), "--clean"]
    try:
        subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Allure report generation failed.")


if __name__ == "__main__":
    raise SystemExit(main())
