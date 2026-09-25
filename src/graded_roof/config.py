from __future__ import annotations

from pathlib import Path

import yaml


def load_config(path: str | Path = "config/production.yaml") -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("configuration root must be a mapping")
    return config
