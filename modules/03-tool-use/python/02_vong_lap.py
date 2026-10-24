"""Module 03 — vòng lặp tool (agentic loop) với nhiều tool, gọi song song.

Lặp: gọi Claude -> nếu stop_reason là "tool_use" thì chạy MỌI tool_use trong response,
gửi MỌI kết quả trong MỘT lượt user -> gọi lại. Dừng khi stop_reason khác "tool_use".

Chạy:  CLAUDE_MOCK=1 uv run python modules/03-tool-use/python/02_vong_lap.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools_mau import REGISTRY, TRA_AQI, TRA_NHIET_DO  # noqa: E402

from claude_vi import ClaudeVi, text_of  # noqa: E402

client = ClaudeVi()
tools = [TRA_AQI, TRA_NHIET_DO]
messages = [{"role": "user", "content": "Hà Nội giờ nóng không, có nên chạy bộ ngoài trời không?"}]

for luot in range(1, 6):  # luôn có giới hạn số lượt: agent không được lặp vô hạn
    msg = client.create(messages=messages, tools=tools)
    print(f"Lượt {luot}: stop_reason={msg.stop_reason}")
    if msg.stop_reason != "tool_use":
        break
    messages.append({"role": "assistant", "content": msg.content})
    results = []
    for block in msg.content:
        if block.type != "tool_use":
            continue
        output = REGISTRY[block.name](**block.input)
        print(f"  chạy {block.name}{block.input} -> {output}")
        results.append({"type": "tool_result", "tool_use_id": block.id,
                        "content": json.dumps(output, ensure_ascii=False)})
    messages.append({"role": "user", "content": results})  # mọi kết quả trong MỘT lượt user
else:
    raise SystemExit("Quá 5 lượt mà chưa xong — dừng để tránh tốn tiền.")

print("\nTrả lời:", text_of(msg))
