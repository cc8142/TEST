import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EnvConfig:
    name: str
    base_url: str
    timeout_sec: float
    verify_ssl: bool


def load_env_config(env_name=None, config_path=None):
    selected = env_name or os.getenv("ENV", "local")
    path = (
        Path(config_path)
        if config_path
        else Path(__file__).resolve().parents[1] / "config" / "environments.json"
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    if selected not in data:
        available = ", ".join(sorted(data.keys()))
        raise ValueError(f"Unknown env '{selected}'. Available: {available}")
    env = data[selected]
    base_url = os.getenv("BASE_URL", env.get("base_url", ""))
    timeout_sec = float(os.getenv("HTTP_TIMEOUT", env.get("timeout_sec", 5)))
    verify_ssl = os.getenv("VERIFY_SSL", str(env.get("verify_ssl", True))).lower() in (
        "1",
        "true",
        "yes",
    )
    return EnvConfig(
        name=selected,
        base_url=base_url,
        timeout_sec=timeout_sec,
        verify_ssl=verify_ssl,
    )
