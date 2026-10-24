# legacy/ — chỉ để đọc

Code mẫu theo cách **cũ** (trước model 5.x), giữ lại để học viên nhận ra khi gặp trong tutorial khác. Không chạy được trên model hiện hành.

| Cách cũ | Vì sao hỏng | Thay bằng |
|---|---|---|
| `temperature=0` | 400 trên model 5.x; bị bỏ khỏi Python SDK ≥1.0 | Prompt rõ ràng + structured outputs |
| `thinking={"type":"enabled","budget_tokens":N}` | Bị bỏ | Adaptive thinking + `output_config.effort` |
| Prefill `{"role":"assistant","content":"{"}` | 400 | `output_config.format` (JSON schema) |
| `tool_choice={"type":"any"}` | 400 trên Fable 5.1, Opus 5.5, Sonnet 5.5 | `auto` + strict tool use |
| `msg.content[0].text` | Block đầu có thể là `thinking` | `text_of(msg)` |
