import os
import requests

from framework.logger import init_logger
from framework.retry import RetryPolicy, run_with_retry
from framework.allure_utils import attach_json, attach_text, step


_DEFAULT_REDACT_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
}


def _get_redact_keys():
    extra = os.getenv("REDACT_KEYS", "")
    keys = {item.strip().lower() for item in extra.split(",") if item.strip()}
    return _DEFAULT_REDACT_KEYS | keys


def _redact_value(value, keys):
    if isinstance(value, dict):
        return _redact_mapping(value, keys)
    if isinstance(value, (list, tuple)):
        return [_redact_value(item, keys) for item in value]
    return value


def _redact_mapping(mapping, keys):
    if not mapping:
        return mapping
    return {
        key: ("***" if str(key).lower() in keys else _redact_value(val, keys))
        for key, val in mapping.items()
    }


def _resolve_url(base_url, path):
    if path.startswith(("http://", "https://")):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base_url}{path}"


class HttpClient:
    def __init__(
        self,
        base_url,
        timeout_sec=5,
        verify_ssl=True,
        default_headers=None,
        retry_policy=None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        if default_headers:
            self.session.headers.update(default_headers)
        self.retry_policy = retry_policy or RetryPolicy(
            retry_on_exceptions=(requests.exceptions.RequestException,)
        )
        self.logger = init_logger("http")

    def request(self, method, path, **kwargs):
        method = method.upper()
        url = _resolve_url(self.base_url, path)
        timeout = kwargs.pop("timeout", self.timeout_sec)
        verify = kwargs.pop("verify", self.verify_ssl)
        redact_keys = _get_redact_keys()
        headers = dict(self.session.headers)
        if kwargs.get("headers"):
            headers.update(kwargs.get("headers", {}))

        with step(f"{method} {path}"):
            request_meta = {
                "method": method,
                "url": url,
                "params": _redact_value(kwargs.get("params"), redact_keys),
                "headers": _redact_mapping(headers, redact_keys),
                "json": _redact_value(kwargs.get("json"), redact_keys),
            }
            if os.getenv("ALLURE_ATTACH", "0") == "1":
                attach_json("request", request_meta)

            def _do_request():
                return self.session.request(method, url, timeout=timeout, verify=verify, **kwargs)

            def _retryable(resp):
                return (
                    method in self.retry_policy.retry_on_methods
                    and resp.status_code in self.retry_policy.retry_on_status
                )

            def _on_retry(attempt, exc, resp):
                if exc:
                    reason = f"{type(exc).__name__}: {exc}"
                elif resp is not None:
                    reason = f"status {resp.status_code}"
                else:
                    reason = "unknown"
                self.logger.warning(
                    "Retrying %s %s (attempt %s/%s) due to %s",
                    method,
                    url,
                    attempt,
                    self.retry_policy.attempts,
                    reason,
                )

            response = run_with_retry(_do_request, self.retry_policy, _retryable, _on_retry)
            self.logger.debug("HTTP %s %s -> %s", method, url, response.status_code)

            if os.getenv("ALLURE_ATTACH", "0") == "1":
                attach_json(
                    "response_meta",
                    {
                        "status_code": response.status_code,
                        "headers": _redact_mapping(dict(response.headers), redact_keys),
                    },
                )
                try:
                    attach_json(
                        "response_body",
                        _redact_value(response.json(), redact_keys),
                    )
                except ValueError:
                    attach_text("response_body", response.text[:2000])
            return response

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)
