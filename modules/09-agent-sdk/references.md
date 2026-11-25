# Nguồn · Module 09

Kiểm ngày **25/11/2026**, với `claude-agent-sdk` **0.2.189** (kèm Claude Code CLI 2.1.332). Nội dung bài viết bằng lời của repo. Docs của Agent SDK nằm ở `code.claude.com/docs/en/agent-sdk/`; đường `platform.claude.com/docs/en/agent-sdk/` chuyển hướng (HTTP 307) sang đó.

| Chủ đề | Nguồn | Kiểm ngày | Dùng cho |
|---|---|---|---|
| Agent SDK là gì, so với Client SDK, CLI và Managed Agents; chạy Claude Code CLI trong process của bạn; không được cho người dùng đăng nhập claude.ai nếu chưa được duyệt; quy tắc đặt tên sản phẩm; Commercial Terms | [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) | 25/11/2026 | Mục 1 |
| Gói kèm sẵn CLI, không cần Node (trừ khi cài từ sdist); xác thực bằng `ANTHROPIC_API_KEY`, không tự đọc `.env`; biến môi trường cho Bedrock, Vertex, Foundry | [Quickstart](https://code.claude.com/docs/en/agent-sdk/quickstart) | 25/11/2026 | Mục 1, `claude_vi.agent_sdk` |
| Tên gói, bản 0.2.189 (25/11/2026), Python ≥ 3.10, giấy phép MIT, kích thước wheel khoảng 165–178 MB | [PyPI claude-agent-sdk](https://pypi.org/project/claude-agent-sdk/) | 25/11/2026 | Mục 1, lý do không thêm vào dependency |
| `query()`, `ClaudeSDKClient`, `ClaudeAgentOptions` (các trường dùng trong bài), loại message và content block, 5 giá trị `ResultMessage.subtype`, `PermissionResultAllow`/`Deny`, `ToolPermissionContext`, `HookMatcher` (gồm `on_failure`), `@tool` và 3 dạng `input_schema`, `create_sdk_mcp_server`, `AgentDefinition`, `ResultError` (từ 0.2.140), `effort`/`thinking`, `max_thinking_tokens` lỗi thời | [Python reference](https://code.claude.com/docs/en/agent-sdk/python); mã nguồn [anthropics/claude-agent-sdk-python v0.2.189](https://github.com/anthropics/claude-agent-sdk-python/tree/v0.2.189) (`types.py`, `__init__.py`, `query.py`) | 25/11/2026 | Mục 2–8, `claude_vi.agent_sdk_mock` |
| Mỗi `AssistantMessage` mang một block; đọc hết luồng; `success` có thể kèm `is_error`; `usage` chỉ gồm vòng lặp chính; `max_turns`/`max_budget_usd` mặc định không giới hạn, cách đếm lượt, kiểm trần sau mỗi response; `query()` ném lỗi sau `ResultMessage` lỗi | [Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) | 25/11/2026 | Mục 2, 6, script 01, 03 |
| Luồng quyền 6 bước, 6 permission mode, `allowed_tools` chỉ duyệt sẵn, glob trong luật allow và deny, luật deny thắng `bypassPermissions`, lời gọi đã duyệt không tới `can_use_tool`, `dontAsk` cho agent không người canh, mode mặc định từ Claude Code 2.1.302, cảnh báo `bypassPermissions` | [Permissions](https://code.claude.com/docs/en/agent-sdk/permissions) | 25/11/2026 | Mục 5, script 02, bài 2, `_duyet` trong mock |
| 10 sự kiện hook của Python, `matcher` chỉ so tên tool (tên chính xác hoặc regex), chữ ký callback, cách chặn bằng `permissionDecision: "deny"`, `{}` là không ý kiến, mở cửa khi callback lỗi trừ khi `on_failure="block"`, `additionalContext` và `systemMessage`, hook `Write|Edit` không bắt được ghi qua `Bash` | [Hooks](https://code.claude.com/docs/en/agent-sdk/hooks) | 25/11/2026 | Mục 5, script 02, bài 2 |
| Tool tự viết: dạng schema đơn giản bắt buộc mọi khoá, cần JSON Schema cho `enum`; SDK kiểm input theo schema trước handler (`Input validation error`, mã nguồn `__init__.py`); handler trả `content`/`is_error`; exception thành kết quả lỗi | [Custom tools](https://code.claude.com/docs/en/agent-sdk/custom-tools) | 25/11/2026 | Mục 4, `cong_cu.py`, bài 3 |
| Tên `mcp__<khoá>__<tool>`, khoá là khoá trong `mcp_servers`; wildcard `mcp__<server>__*`; tool MCP chưa duyệt thì thấy nhưng không gọi được | [MCP](https://code.claude.com/docs/en/agent-sdk/mcp) | 25/11/2026 | Mục 4 |
| Tên tool dựng sẵn; `Task` đổi thành `Agent`; `Glob`/`Grep` mặc định không có trên Linux, macOS, WSL | [Tools reference](https://code.claude.com/docs/en/tools-reference) | 25/11/2026 | Mục 3 |
| `session_id`, `resume`, `continue_conversation`, `fork_session`, nơi lưu phiên, resume trên máy khác | [Sessions](https://code.claude.com/docs/en/agent-sdk/sessions) | 25/11/2026 | Mục 6, script 03 |
| `total_cost_usd` là ước tính phía client; khử trùng theo `message_id`; `output_tokens` theo bước là giá trị giữ chỗ; phiên resume hoặc fork đã gồm chi phí cũ; subagent tính vào `total_cost_usd` | [Cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking) | 25/11/2026 | Mục 7, script 03, bài 1 |
| System prompt mặc định tối giản; preset `claude_code` | [Modifying system prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts) | 25/11/2026 | Mục 3 |
| `setting_sources` mặc định nạp mọi nguồn; `[]` bỏ user/project/local nhưng policy, `~/.claude.json`, auto memory vẫn nạp (mục "What settingSources does not control"); cần `"project"` để nạp `CLAUDE.md`; cách ly nhiều khách hàng | [Claude Code features](https://code.claude.com/docs/en/agent-sdk/claude-code-features) | 25/11/2026 | Mục 3 |
| Subagent: `AgentDefinition`, tool `Agent`, context riêng, chỉ trả message cuối | [Subagents](https://code.claude.com/docs/en/agent-sdk/subagents) | 25/11/2026 | Mục 8 |
| Structured outputs trong SDK | [Structured outputs](https://code.claude.com/docs/en/agent-sdk/structured-outputs) | 25/11/2026 | Mục 8 |
| Mỗi `query()` một process CLI; gợi ý 1 GiB RAM, 5 GiB đĩa, 1 CPU mỗi agent; nguy cơ lộ ngữ cảnh giữa khách hàng | [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting) | 25/11/2026 | Mục 3, 7 |
| Prompt injection và lỗi của model; nhiều lớp bảo vệ, quyền tối thiểu, credential qua proxy | [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment) | 25/11/2026 | Mục 8 |
| Đổi tên Claude Code SDK thành Claude Agent SDK ở 0.1.0; `can_use_tool` chạy với prompt dạng chuỗi từ 0.2.140; `on_failure` từ 0.2.177 | [CHANGELOG v0.2.189](https://github.com/anthropics/claude-agent-sdk-python/blob/v0.2.189/CHANGELOG.md) | 25/11/2026 | Mục 5, bảng "Điều gì đã thay đổi" |
| Tokenizer từ model 4.7, `display` mặc định `"omitted"` từ Opus 4.7, luật `budget_tokens` trên model 5.x | [module 06 references](../06-cost/references.md), [module 07 references](../07-thinking/references.md) | 25/11/2026, 09/11/2026 | Bảng "Điều gì đã thay đổi" |

## Chỗ docs và mã nguồn chưa khớp (ghi lại, chưa dùng trong bài)

- Thời gian chờ mặc định của hook: docs ghi 600 giây (30 giây cho `UserPromptSubmit`); comment trong `types.py` ghi 60.
- Cách đếm lượt: docs Agent loop đếm mỗi lượt gọi tool cộng một lượt trả lời cuối; docstring của `max_turns` trong mã nguồn mô tả khác. Bài theo docs.
- Ví dụ `can_use_tool` trong docs User input vẫn dùng prompt dạng stream kèm hook giả làm "workaround"; CHANGELOG 0.2.140 nói `can_use_tool` đã chạy với prompt dạng chuỗi. Script dùng prompt dạng chuỗi theo CHANGELOG; chưa chạy thật để kiểm.
- CHANGELOG dừng ở 0.2.178; các bản 0.2.179–0.2.189 chỉ nâng bản CLI kèm theo (theo commit trên GitHub).

## Mock khác SDK thật ở đâu

- Không chạy CLI, không có tool dựng sẵn, không có `ClaudeSDKClient`, không có luật ask, không xử lý `interrupt` của `PermissionResultDeny`.
- Mỗi lượt mock gọi đúng một tool; SDK thật có thể gọi nhiều tool trong một lượt.
- Kiểm input theo schema chỉ ở mức tối thiểu (trường bắt buộc, kiểu, `enum`); SDK thật dùng `jsonschema`.
- `continue_conversation` cùng `resume`: mock ném `ValueError`; docs chỉ ghi hai tuỳ chọn loại trừ nhau.
- Mock luôn điền `usage` và `total_cost_usd`; SDK thật để các trường này `Optional`.
- Mock ghi lời gọi bị hook từ chối vào `permission_denials`; chưa kiểm SDK thật có ghi trường hợp này hay không.
- Số token, chi phí và nội dung trả lời là giả lập; luồng message, tên lớp, tên trường và thứ tự xét quyền thì theo docs.

## Chi phí ước tính

3 script, 9 lần chạy agent (01: 2, 02: 3, 03: 4), khoảng 18 lượt gọi model với `claude-haiku-5-5`. Mỗi lần chạy có trần `max_budget_usd=0.01` (hai lần ở script 03 cố ý đặt trần rất nhỏ), nên trường hợp xấu nhất khoảng $0,09 cộng phần vượt trần nhỏ. Nếu mỗi lượt tới khoảng 5.000 token input và 500 token output, cả module khoảng 18 × ($0,0005 + $0,00025) ≈ $0,014. Kích thước system prompt và định nghĩa tool mà CLI gửi đi chưa đo. Đây là ước tính, chưa chạy thật.
