"""Bài 1 — chọn cấu hình thinking theo luật từng model.

Đọc luật từ config/models.yaml qua load_models()["models"][model]["rules"]. KHÔNG viết cứng tên model:
khi có model mới, chỉ YAML đổi, code của bạn vẫn đúng.

it_thinking_nhat(model) -> dict tham số cho client.create(**...) để model suy nghĩ ít nhất có thể
    - Luôn có "output_config": {"effort": "low"}.
    - Nếu rules["thinking_disabled_allowed"]: thêm "thinking": {"type": "disabled"}.
    - Ngược lại nếu rules["between_tools_allowed"]: thêm "thinking": {"type": "between_tools"}.
    - Ngược lại: không có trường thinking (model không tắt được, effort là núm vặn duy nhất).

xem_tom_tat(model, effort=None) -> dict để đọc được tóm tắt thinking
    - "thinking": {"type": "adaptive", "display": "summarized"}
    - effort khác None thì thêm "output_config": {"effort": effort}.

Cả hai: model không có trong YAML hoặc status khác "active" -> raise ValueError.

Chấm:  CHAM=exercises uv run pytest modules/07-thinking -q
"""
from __future__ import annotations

from typing import Any

from claude_vi import load_models  # noqa: F401


def it_thinking_nhat(model: str) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 1")


def xem_tom_tat(model: str, effort: str | None = None) -> dict[str, Any]:
    raise NotImplementedError("TODO: bài 1")
