"""Tiện ích chấm bài tập, dùng chung cho test của mọi module.

    uv run pytest modules/NN-ten -q                    # chấm lời giải (CI)
    CHAM=exercises uv run pytest modules/NN-ten -q     # chấm bài của học viên
"""
from __future__ import annotations

import copy
import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from .client import ClaudeVi
from .config import Settings
from .mock import MockAnthropic

SETTINGS = Settings(model="claude-haiku-5-5", max_tokens=512, mock=True, record=False)


def nap(module_dir: Path, ten: str) -> ModuleType:
    """Nạp file bài `ten`.py từ solutions/ (mặc định) hoặc thư mục trong biến CHAM."""
    thu_muc = os.getenv("CHAM", "solutions")
    path = Path(module_dir) / thu_muc / f"{ten}.py"
    ten_module = f"cham_{Path(module_dir).name}_{thu_muc}_{ten}".replace("-", "_")
    spec = importlib.util.spec_from_file_location(ten_module, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ten_module] = mod  # dataclass trong file bài cần module có trong sys.modules
    spec.loader.exec_module(mod)
    return mod


def tao_client(**mock_kwargs: Any) -> tuple[ClaudeVi, MockAnthropic]:
    """Client mock ghi lại bản sao sâu tham số của mỗi request vào mock.da_gui."""
    mock = MockAnthropic(**mock_kwargs)
    goc = mock.messages.create
    mock.da_gui = []

    def create(**params: Any) -> Any:
        mock.da_gui.append(copy.deepcopy(params))
        return goc(**params)

    mock.messages.create = create
    return ClaudeVi(settings=SETTINGS, client=mock), mock
