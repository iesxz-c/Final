"""Phase 0 health check.

Verifies the Python environment, minimal dependencies, project layout,
configuration loading, and presence of the EXTERNAL dataset directories.

Usage:
    python scripts/health_check.py [--config PATH]

Exit codes: 0 = ready, 1 = critical failure, 2 = warnings only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _section(title: str) -> None:
    print(f"\n== {title} ==")


def check_python() -> bool:
    _section("Python")
    print(f"  version: {sys.version.split()[0]}")
    if sys.version_info < (3, 9):
        print("  [FAIL] Python >= 3.9 required")
        return False
    print("  [PASS]")
    return True


def check_dependencies() -> bool:
    _section("Dependencies")
    try:
        import yaml

        print(f"  pyyaml: {yaml.__version__} [PASS]")
        return True
    except ImportError:
        print("  pyyaml: missing [FAIL] -> pip install -r requirements.txt")
        return False


def check_layout() -> bool:
    _section("Project layout")
    expected = [
        "src",
        "src/pipeline",
        "src/evidence",
        "src/agents",
        "src/agents/query_planning",
        "src/agents/evidence_retrieval",
        "src/agents/temporal_correlation",
        "src/agents/verification_report",
        "config",
        "scripts",
        "data",
    ]
    ok = True
    for rel in expected:
        if (PROJECT_ROOT / rel).is_dir():
            print(f"  {rel}: [PASS]")
        else:
            print(f"  {rel}: [FAIL] missing")
            ok = False
    return ok


def check_config(config_path: str | None) -> dict | None:
    _section("Configuration")
    try:
        from src.settings import load_config

        config = load_config(config_path)
        print(f"  loaded: {config['project']['config_path']}")
        print(f"  project root: {config['project']['root']}")
        print("  [PASS]")
        return config
    except Exception as exc:  # noqa: BLE001 - report any config failure
        print(f"  [FAIL] {exc}")
        return None


def check_datasets(config: dict | None) -> bool:
    _section("External datasets (informational)")
    if config is None:
        print("  [SKIP] config unavailable")
        return False

    from src.settings import dataset_paths

    paths = dataset_paths(config)
    ok = True
    for label, path in paths.items():
        if path is None or str(path) in ("", "."):
            print(f"  {label}: [FAIL] no path configured")
            ok = False
        elif path.is_dir():
            print(f"  {label}: {path} [PASS]")
        else:
            print(f"  {label}: {path} [WARN] not found (expected: dataset is external)")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 0 environment health check")
    parser.add_argument("--config", default=None, help="path to a config file")
    args = parser.parse_args()

    print(f"Health check - {PROJECT_ROOT}")

    critical = [
        check_python(),
        check_dependencies(),
        check_layout(),
    ]
    config = check_config(args.config)
    critical.append(config is not None)

    warnings_only = not check_datasets(config)

    failures = [not ok for ok in critical]
    if any(failures):
        print("\nSummary: FAILURES detected")
        return 1

    print("\nSummary: environment ready (dataset warnings are non-fatal).")
    return 2 if warnings_only else 0


if __name__ == "__main__":
    sys.exit(main())