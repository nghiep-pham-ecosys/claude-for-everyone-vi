"""Module 07 — giảm hoặc tắt thinking: mỗi model một luật.

Không có một câu lệnh "tắt thinking" chung cho mọi model 5.x:
- Haiku 5.5:   {"type": "disabled"}, chỉ ở effort high trở xuống.
- Sonnet 5.5:  {"type": "between_tools"} tắt phần suy nghĩ đầu lượt; "disabled" trả 400.
- Opus 5.5, Fable 5.1, Fable 5.2: không tắt được. Núm vặn duy nhất là effort.

Phần 1 chỉ kiểm luật tại máy (claude_vi đọc config/models.yaml), không gửi request nào.
Phần 2 gửi một request với model mặc định.

Chạy:  CLAUDE_MOCK=1 uv run python modules/07-thinking/python/02_tat_thinking.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, ModelRuleError, check_request, load_models  # noqa: E402

CACH = {
    "disabled": {"thinking": {"type": "disabled"}},
    "between_tools": {"thinking": {"type": "between_tools"}},
    "disabled+xhigh": {"thinking": {"type": "disabled"}, "output_config": {"effort": "xhigh"}},
    "effort low": {"output_config": {"effort": "low"}},
}
models = [m for m, e in load_models()["models"].items() if e.get("status") == "active"]

print(f"{'model':<20}" + "".join(f"{k:>16}" for k in CACH))
for model in models:
    o = []
    for extra in CACH.values():
        try:
            check_request({"model": model, "messages": [{"role": "user", "content": "x"}], **extra})
            o.append("được")
        except ModelRuleError:
            o.append("400")
    print(f"{model:<20}" + "".join(f"{x:>16}" for x in o))

client = ClaudeVi()
model = client.settings.model
rules = load_models()["models"][model]["rules"]
if rules.get("thinking_disabled_allowed"):
    it_nhat = CACH["disabled"]
elif rules.get("between_tools_allowed"):
    it_nhat = CACH["between_tools"]
else:
    it_nhat = CACH["effort low"]
msg = client.ask("Thủ đô của Việt Nam?", **it_nhat)
print(f"\n{model} với {it_nhat}: blocks={[b.type for b in msg.content]}, output={msg.usage.output_tokens} token")
