from dataclasses import dataclass
import random
import time


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    backoff_sec: float = 0.2
    max_backoff_sec: float = 2.0
    jitter_sec: float = 0.1
    retry_on_status: tuple = (408, 429, 500, 502, 503, 504)
    retry_on_exceptions: tuple = (Exception,)
    retry_on_methods: tuple = ("GET", "HEAD", "PUT", "DELETE", "OPTIONS")


def _sleep_backoff(attempt, policy):
    if policy.backoff_sec <= 0:
        return
    backoff = min(policy.backoff_sec * (2 ** (attempt - 1)), policy.max_backoff_sec)
    if policy.jitter_sec:
        backoff += random.uniform(0, policy.jitter_sec)
    time.sleep(backoff)


def run_with_retry(func, policy, is_retryable=None, on_retry=None):
    last_exc = None
    for attempt in range(1, policy.attempts + 1):
        try:
            result = func()
            if is_retryable and is_retryable(result) and attempt < policy.attempts:
                if on_retry:
                    on_retry(attempt, None, result)
                _sleep_backoff(attempt, policy)
                continue
            return result
        except policy.retry_on_exceptions as exc:
            last_exc = exc
            if attempt >= policy.attempts:
                raise
            if on_retry:
                on_retry(attempt, exc, None)
            _sleep_backoff(attempt, policy)
    if last_exc:
        raise last_exc
