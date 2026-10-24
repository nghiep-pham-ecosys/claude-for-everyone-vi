"""Đọc config/models.yaml và biến môi trường."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
MODELS_FILE = REPO_ROOT / "config" / "models.yaml"


@lru_cache(maxsize=1)
def load_models() -> dict[str, Any]:
    with MODELS_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass(frozen=True)
class Settings:
    model: str
    max_tokens: int
    mock: bool
    record: bool

    @classmethod
    def from_env(cls) -> "Settings":
        cfg = load_models()
        return cls(
            model=os.getenv("CLAUDE_MODEL", cfg["default_model"]),
            max_tokens=int(os.getenv("MAX_TOKENS", "1024")),
            mock=os.getenv("CLAUDE_MOCK", "0") == "1",
            record=os.getenv("CLAUDE_RECORD", "0") == "1",
        )
