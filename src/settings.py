"""Configuration loading for the CCTV investigation framework.

The dataset is external to the repository; all paths are resolved at runtime
and are overridable via environment variables so no path is hard-coded.
"""

from __future__ import annotations

import os
from pathlib import Path

try:  # pragma: no cover - import presence is checked in health-check too
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
EXAMPLE_CONFIG_PATH = CONFIG_DIR / "config.example.yaml"
LOCAL_CONFIG_PATH = CONFIG_DIR / "config.yaml"

# Environment variables used to point at config and datasets.
CONFIG_ENV_VAR = "CCTV_CASE_CONFIG"
ANOMALY_VIDEOS_ENV = "CCTV_ANOMALY_VIDEOS_DIR"
NORMAL_VIDEOS_ENV = "CCTV_NORMAL_VIDEOS_DIR"


class ConfigError(RuntimeError):
    """Raised when the configuration cannot be located or parsed."""


def _resolve_config_path(path: str | os.PathLike | None) -> Path:
    """Pick the config file: explicit argument, env var, local override, example."""
    if path is not None:
        candidate = Path(path)
    elif os.environ.get(CONFIG_ENV_VAR):
        candidate = Path(os.environ[CONFIG_ENV_VAR])
    elif LOCAL_CONFIG_PATH.exists():
        candidate = LOCAL_CONFIG_PATH
    else:
        candidate = EXAMPLE_CONFIG_PATH

    if not candidate.exists():
        raise ConfigError(f"Config file not found: {candidate}")
    return candidate


def _apply_dataset_env_overrides(config: dict) -> dict:
    env_map = {
        ANOMALY_VIDEOS_ENV: ("datasets", "anomaly_videos", "path"),
        NORMAL_VIDEOS_ENV: ("datasets", "normal_videos", "path"),
    }
    for env_name, keys in env_map.items():
        value = os.environ.get(env_name)
        if value:
            config.get("datasets", {}).get(keys[1], {}) if len(keys) == 3 else None
            section = config.setdefault("datasets", {})
            leaf = section.setdefault(keys[1], {})
            leaf[keys[2]] = value
    return config


def load_config(path: str | os.PathLike | None = None) -> dict:
    """Load and return the configuration as a plain dict."""
    if yaml is None:
        raise ConfigError(
            "PyYAML is required. Install dependencies with: pip install -r requirements.txt"
        )

    config_path = _resolve_config_path(path)
    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    config.setdefault("project", {})
    config["project"].setdefault("name", "Agentic_Framework_CCTV_Crime_Investigation")
    config["project"]["root"] = str(PROJECT_ROOT)
    config["project"]["config_path"] = str(config_path)

    return _apply_dataset_env_overrides(config)


def dataset_paths(config: dict) -> dict:
    """Return resolved anomaly/normal dataset paths in pathlib form."""
    datasets = config.get("datasets", {})
    return {
        "anomaly_videos": Path(datasets.get("anomaly_videos", {}).get("path", "")),
        "normal_videos": Path(datasets.get("normal_videos", {}).get("path", "")),
    }