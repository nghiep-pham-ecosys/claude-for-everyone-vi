"""Module 07: reduce or turn off thinking: each model has its own rules (tat_thinking = turn off thinking).

There is no single "turn off thinking" switch for every 5.x model:
- Haiku 5.5:   {"type": "disabled"}, only at effort high or lower.
- Sonnet 5.5:  {"type": "between_tools"} turns off the thinking at the start of the turn; "disabled" returns 400.
- Opus 5.5, Fable 5.1, Fable 5.2: cannot be turned off. The only knob is effort.

Part 1 only checks the rules on your machine (claude_vi reads config/models.yaml) and sends no request.
Part 2 sends one request with the default model.

Run:  CLAUDE_MOCK=1 uv run python en/modules/07-thinking/python/02_tat_thinking.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "py"))

from claude_vi import ClaudeVi, ModelRuleError, check_request, load_models  # noqa: E402

WAYS = {
    "disabled": {"thinking": {"type": "disabled"}},
    "between_tools": {"thinking": {"type": "between_tools"}},
    "disabled+xhigh": {"thinking": {"type": "disabled"}, "output_config": {"effort": "xhigh"}},
    "effort low": {"output_config": {"effort": "low"}},
}
models = [m for m, e in load_models()["models"].items() if e.get("status") == "active"]

print(f"{'model':<20}" + "".join(f"{k:>16}" for k in WAYS))
for model in models:
    o = []
    for extra in WAYS.values():
        try:
            check_request({"model": model, "messages": [{"role": "user", "content": "x"}], **extra})
            o.append("ok")
        except ModelRuleError:
            o.append("400")
    print(f"{model:<20}" + "".join(f"{x:>16}" for x in o))

client = ClaudeVi()
model = client.settings.model
rules = load_models()["models"][model]["rules"]
if rules.get("thinking_disabled_allowed"):
    least = WAYS["disabled"]
elif rules.get("between_tools_allowed"):
    least = WAYS["between_tools"]
else:
    least = WAYS["effort low"]
msg = client.ask("What is the capital of Vietnam?", **least)
print(f"\n{model} with {least}: blocks={[b.type for b in msg.content]}, output={msg.usage.output_tokens} tokens")
