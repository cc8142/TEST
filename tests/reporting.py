import html
import json
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


def _extract_details(elem):
    if elem is None:
        return ""
    message = elem.get("message", "")
    text = (elem.text or "").strip()
    if message and text:
        return f"{message}: {text.splitlines()[0]}"
    if message:
        return message
    if text:
        return text.splitlines()[0]
    return ""


def _classify_failure(details):
    if not details:
        return "unknown"
    lowered = details.lower()
    if "timeout" in lowered or "timed out" in lowered:
        return "timeout"
    if any(
        token in lowered
        for token in (
            "connectionerror",
            "readtimeout",
            "proxyerror",
            "dns",
            "ssl",
            "playwright",
        )
    ):
        return "infra"
    if "assert" in lowered or "expected" in lowered:
        return "assertion"
    return "error"


def parse_junit(junit_path):
    junit_path = Path(junit_path)
    if not junit_path.exists():
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "time": 0.0,
            "items": [],
            "by_suite": [],
            "slow_tests": [],
            "reruns_total": 0,
            "flaky_total": 0,
            "failed_breakdown": [],
        }

    tree = ET.parse(junit_path)
    root = tree.getroot()
    if root.tag == "testsuite":
        suites = [root]
    else:
        suites = root.findall("testsuite")

    items = []
    by_suite = {}
    total = 0
    failed = 0
    skipped = 0
    total_time = 0.0
    reruns_total = 0
    flaky_total = 0
    failed_breakdown = {}

    for suite in suites:
        suite_name = suite.get("name", "suite")
        suite_total = int(suite.get("tests", 0))
        suite_failed = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
        suite_skipped = int(suite.get("skipped", 0))
        suite_time = float(suite.get("time", 0))
        total += suite_total
        failed += suite_failed
        skipped += suite_skipped
        total_time += suite_time

        stats = by_suite.setdefault(
            suite_name,
            {"suite": suite_name, "total": 0, "failed": 0, "skipped": 0, "time": 0.0},
        )
        stats["total"] += suite_total
        stats["failed"] += suite_failed
        stats["skipped"] += suite_skipped
        stats["time"] += suite_time

        for case in suite.findall("testcase"):
            case_name = case.get("name", "")
            classname = case.get("classname", "")
            time_sec = float(case.get("time", 0))
            failure = case.find("failure")
            error = case.find("error")
            skipped_elem = case.find("skipped")
            reruns = len(case.findall("rerun"))
            flaky = case.find("flaky") is not None or reruns > 0
            status = "PASS"
            details = ""
            if failure is not None or error is not None:
                status = "FAIL"
                details = _extract_details(failure or error)
            elif skipped_elem is not None:
                status = "SKIP"
                details = _extract_details(skipped_elem)
            if status == "FAIL":
                category = _classify_failure(details)
                failed_breakdown[category] = failed_breakdown.get(category, 0) + 1
            if reruns:
                reruns_total += reruns
            if flaky:
                flaky_total += 1
            test_id = f"{classname}::{case_name}" if classname else case_name
            items.append(
                {
                    "suite": suite_name,
                    "test": test_id,
                    "status": status,
                    "time": time_sec,
                    "details": details,
                    "reruns": reruns,
                    "flaky": flaky,
                }
            )

    passed = max(total - failed - skipped, 0)
    slow_tests = sorted(items, key=lambda x: x["time"], reverse=True)[:5]
    by_suite_list = sorted(by_suite.values(), key=lambda x: x["suite"])
    failed_breakdown_list = [
        {"category": name, "count": count}
        for name, count in sorted(failed_breakdown.items())
    ]

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "time": total_time,
        "items": items,
        "by_suite": by_suite_list,
        "slow_tests": slow_tests,
        "reruns_total": reruns_total,
        "flaky_total": flaky_total,
        "failed_breakdown": failed_breakdown_list,
    }


def build_summary(junit_path, context):
    parsed = parse_junit(junit_path)
    items = parsed["items"]
    if not items:
        items = [
            {
                "suite": "all",
                "test": "all",
                "status": "PASS",
                "time": 0.0,
                "details": "All checks passed",
            }
        ]

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "run_id": context.get("run_id", ""),
        "env": context.get("env", ""),
        "suite": context.get("suite", ""),
        "base_url": context.get("base_url", ""),
        "total": parsed["total"],
        "passed": parsed["passed"],
        "failed": parsed["failed"],
        "skipped": parsed["skipped"],
        "duration_sec": context.get("duration_sec", parsed["time"]),
        "items": items,
        "by_suite": parsed["by_suite"],
        "slow_tests": parsed["slow_tests"],
        "reruns_total": parsed.get("reruns_total", 0),
        "flaky_total": parsed.get("flaky_total", 0),
        "failed_breakdown": parsed.get("failed_breakdown", []),
        "meta": {
            "python": context.get("python", ""),
            "platform": context.get("platform", ""),
            "pytest": context.get("pytest", ""),
            "command": context.get("command", ""),
            "workers": context.get("workers", ""),
            "reruns": context.get("reruns", ""),
            "browser": context.get("browser", ""),
            "headed": context.get("headed", ""),
        },
    }


def _fmt_seconds(value):
    try:
        return f"{float(value):.2f}s"
    except (TypeError, ValueError):
        return "0.00s"


def _status_class(status):
    if status == "PASS":
        return "status-ok"
    if status == "SKIP":
        return "status-skip"
    return "status-fail"


def write_reports(summary, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "summary.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    meta = summary.get("meta", {})
    meta_rows = "".join(
        f"<tr><th>{html.escape(str(k))}</th><td class=\"mono\">"
        f"{html.escape(str(v))}</td></tr>"
        for k, v in [
            ("Run ID", summary.get("run_id", "")),
            ("Generated", summary.get("generated_at", "")),
            ("Env", summary.get("env", "")),
            ("Suite", summary.get("suite", "")),
            ("Base URL", summary.get("base_url", "")),
            ("Python", meta.get("python", "")),
            ("Pytest", meta.get("pytest", "")),
            ("Platform", meta.get("platform", "")),
            ("Command", meta.get("command", "")),
            ("Workers", meta.get("workers", "")),
            ("Reruns", meta.get("reruns", "")),
            ("Browser", meta.get("browser", "")),
            ("Headed", meta.get("headed", "")),
        ]
    )

    suite_rows = "".join(
        f"<tr><td>{html.escape(suite['suite'])}</td>"
        f"<td>{suite['total']}</td>"
        f"<td class=\"status-fail\">{suite['failed']}</td>"
        f"<td class=\"status-skip\">{suite['skipped']}</td>"
        f"<td>{_fmt_seconds(suite['time'])}</td></tr>"
        for suite in summary.get("by_suite", [])
    )

    slow_rows = "".join(
        f"<tr><td class=\"mono\">{html.escape(test['test'])}</td>"
        f"<td>{_fmt_seconds(test['time'])}</td></tr>"
        for test in summary.get("slow_tests", [])
    )

    breakdown = summary.get("failed_breakdown", [])
    if breakdown:
        breakdown_rows = "".join(
            f"<tr><td>{html.escape(item['category'])}</td><td>{item['count']}</td></tr>"
            for item in breakdown
        )
    else:
        breakdown_rows = "<tr><td colspan=\"2\">No failures</td></tr>"

    item_rows = "".join(
        f"<tr>"
        f"<td>{html.escape(item['suite'])}</td>"
        f"<td class=\"mono\">{html.escape(item['test'])}</td>"
        f"<td class=\"{_status_class(item['status'])}\">"
        f"{html.escape(item['status'])}</td>"
        f"<td>{_fmt_seconds(item['time'])}</td>"
        f"<td>{item.get('reruns', 0)}</td>"
        f"<td>{'yes' if item.get('flaky') else ''}</td>"
        f"<td>{html.escape(item.get('details', ''))}</td>"
        f"</tr>"
        for item in summary.get("items", [])
    )

    report_html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Automation Summary</title>
    <style>
      :root {{
        --bg: #f4f3f0;
        --text: #1d1b17;
        --card: #ffffff;
        --ok: #1b7f5a;
        --fail: #b23b3b;
        --skip: #8a6d3b;
        --border: #e2ded6;
      }}
      body {{
        font-family: "IBM Plex Sans", "Segoe UI", "Verdana", sans-serif;
        margin: 24px;
        background: var(--bg);
        color: var(--text);
      }}
      h1 {{
        margin-bottom: 8px;
      }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 12px;
        margin: 12px 0 20px 0;
      }}
      .card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
      }}
      .card h3 {{
        margin: 0;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }}
      .card p {{
        margin: 6px 0 0 0;
        font-size: 20px;
      }}
      table {{
        border-collapse: collapse;
        width: 100%;
        background: var(--card);
        border: 1px solid var(--border);
        margin-bottom: 20px;
      }}
      th, td {{
        border-bottom: 1px solid var(--border);
        padding: 8px 10px;
        text-align: left;
        vertical-align: top;
      }}
      th {{
        background: #efece5;
        font-weight: 600;
      }}
      .mono {{
        font-family: "Consolas", "Courier New", monospace;
        font-size: 12px;
        word-break: break-all;
      }}
      .status-ok {{ color: var(--ok); font-weight: 600; }}
      .status-fail {{ color: var(--fail); font-weight: 600; }}
      .status-skip {{ color: var(--skip); font-weight: 600; }}
    </style>
  </head>
  <body>
    <h1>Automation Summary</h1>
    <p>Generated: {html.escape(summary.get("generated_at", ""))}</p>

    <div class="grid">
      <div class="card"><h3>Total</h3><p>{summary.get("total", 0)}</p></div>
      <div class="card"><h3>Passed</h3><p class="status-ok">{summary.get("passed", 0)}</p></div>
      <div class="card"><h3>Failed</h3><p class="status-fail">{summary.get("failed", 0)}</p></div>
      <div class="card"><h3>Skipped</h3><p class="status-skip">{summary.get("skipped", 0)}</p></div>
      <div class="card"><h3>Reruns</h3><p>{summary.get("reruns_total", 0)}</p></div>
      <div class="card"><h3>Flaky</h3><p>{summary.get("flaky_total", 0)}</p></div>
      <div class="card"><h3>Duration</h3><p>{_fmt_seconds(summary.get("duration_sec", 0))}</p></div>
    </div>

    <h2>Run Context</h2>
    <table>
      <tbody>
        {meta_rows}
      </tbody>
    </table>

    <h2>Suite Breakdown</h2>
    <table>
      <thead>
        <tr><th>Suite</th><th>Total</th><th>Failed</th><th>Skipped</th><th>Time</th></tr>
      </thead>
      <tbody>
        {suite_rows}
      </tbody>
    </table>

    <h2>Slowest Tests</h2>
    <table>
      <thead>
        <tr><th>Test</th><th>Time</th></tr>
      </thead>
      <tbody>
        {slow_rows}
      </tbody>
    </table>

    <h2>Failure Breakdown</h2>
    <table>
      <thead>
        <tr><th>Category</th><th>Count</th></tr>
      </thead>
      <tbody>
        {breakdown_rows}
      </tbody>
    </table>

    <h2>Test Details</h2>
    <table>
      <thead>
        <tr><th>Suite</th><th>Test</th><th>Status</th><th>Time</th><th>Reruns</th><th>Flaky</th><th>Details</th></tr>
      </thead>
      <tbody>
        {item_rows}
      </tbody>
    </table>
  </body>
</html>
"""
    (out / "summary.html").write_text(report_html, encoding="utf-8")
