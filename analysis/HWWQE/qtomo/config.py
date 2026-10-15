"""Configuration loader. All configuration lives in ``config/*.yaml``
(PLAN.md rule 5); relative paths in the YAML files are relative to the
analysis root (the directory holding PLAN.md)."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"


def load(name):
    """Return the parsed ``config/<name>.yaml`` as a dict."""
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path) as handle:
        return yaml.safe_load(handle)


def constants():
    return load("constants")


def resolve(path):
    """Absolute path for a path given relative to the analysis root."""
    path = Path(path)
    return path if path.is_absolute() else ROOT / path
