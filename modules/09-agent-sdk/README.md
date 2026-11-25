# 09 · Agent SDK

**Loại:** Learn + Build · **Thời lượng:** khoảng 2 giờ · **Cần:** module 03, 06, 07 và 08 · **Chi phí:** $0 ở mock mode; khi chạy thật, mỗi lần chạy agent có trần `max_budget_usd=0.01`, cả module ước tính khoảng $0,02 (chưa đo, xem [references.md](references.md))

## Mục tiêu

Sau module này bạn:

- Biết Agent SDK là gì, khác Client SDK (`anthropic`, các module trước) ở đâu, và khi nào nên dùng.
- Chạy được một agent bằng `query()` và đọc đúng luồng message: `SystemMessage` → `AssistantMessage` / `UserMessage` → `ResultMessage`.
- Viết tool riêng bằng `@tool` và `create_sdk_mcp_server`, gọi đúng tên `mcp__<server>__<tool>`.
- Quyết định tool nào được chạy bằng `allowed_tools`, `disallowed_tools`, `permission_mode`, `can_use_tool` và hook `PreToolUse`, theo đúng thứ tự SDK xét.
- Đặt trần `max_turns` và `max_budget_usd`, xử lý `ResultError`, nối tiếp phiên bằng `resume`.
- Đọc chi phí của một lần chạy mà không cộng trùng.

| Learn | Build |
|---|---|
| Đọc mục 1–8, chạy 3 script trong `python/` | Làm 3 bài trong `exercises/`, chấm bằng test |

## Vì sao học cái này

Ở module 08 bạn tự viết vòng lặp agent: gửi request, đọc `stop_reason`, chạy tool, gửi `tool_result`, đếm lượt, cộng chi phí, chặn tool nguy hiểm. **Agent SDK** làm phần lớn việc đó cho bạn. Nó là thư viện chạy cùng vòng lặp, cùng bộ tool và cùng cách quản lý context như Claude Code, gọi được từ Python hoặc TypeScript.

Đổi lại, vòng lặp bị che đi. Lỗi khó thấy hơn: một tool chạy mà bạn tưởng đã chặn, một lần chạy không có trần chi phí, một agent đọc file cấu hình của máy bạn mà bạn không biết. Module này dạy những nút điều khiển đó.

## Tối thiểu chạy được

```bash
CLAUDE_MOCK=1 uv run python modules/09-agent-sdk/python/01_query_dau_tien.py
```

| Script | Ý chính |
|---|---|
| [`01_query_dau_tien.py`](python/01_query_dau_tien.py) | `query()`, đọc hết luồng message, `ResultMessage` (số lượt, chi phí ước tính, câu trả lời) |
| [`02_quyen_va_hook.py`](python/02_quyen_va_hook.py) | `allowed_tools`, `can_use_tool` (kể cả `updated_input`), hook `PreToolUse` chặn theo nội dung |
| [`03_gioi_han_va_phien.py`](python/03_gioi_han_va_phien.py) | `max_turns`, `max_budget_usd`, `ResultError`, `resume` và chi phí của phiên nối tiếp |

[`cong_cu.py`](python/cong_cu.py) chứa phần dùng chung: hai tool của trợ lý phòng thí nghiệm hư cấu (`tra_lich` chỉ đọc, `ghi_nhat_ky` có tác dụng phụ) và `options_co_ban()`.

**Về mock của module này.** Gói `claude-agent-sdk` không nằm trong dependency của repo: mỗi wheel khoảng 165–178 MB vì kèm sẵn Claude Code CLI. Ở mock mode, `claude_vi.agent_sdk.nap_sdk()` trả về `claude_vi.agent_sdk_mock`, có cùng tên lớp và tên trường với SDK thật (bản 0.2.189) ở phần bài học dùng tới. Mock không chạy CLI và không có tool dựng sẵn. Mỗi lượt nó gọi **một** tool tự viết chưa gọi, theo thứ tự trong `mcp_servers`, rồi trả lời. Input của tool: giá trị `enum` khớp từ khoá trong prompt; chuỗi tự do thì lấy chính prompt. SDK thật có thể gọi nhiều tool trong một lượt; mock luôn gọi một. Số token và chi phí là của mock; giá đọc từ [`config/models.yaml`](../../config/models.yaml).

Chạy thật (tốn phí API, tuỳ chọn): `uv pip install claude-agent-sdk`, đặt `ANTHROPIC_API_KEY`, bỏ `CLAUDE_MOCK=1`.

## 1. Agent SDK, Client SDK hay Claude Code

| | Client SDK (`anthropic`) | Agent SDK (`claude-agent-sdk`) |
|---|---|---|
| Vòng lặp tool | Bạn tự viết (module 03, 08) | SDK chạy cho bạn |
| Tool dựng sẵn | Không (trừ server tool) | Có: đọc/sửa file, chạy lệnh, tìm web... |
| Chạy ở đâu | Gọi thẳng API | Chạy Claude Code CLI như một process con của chương trình bạn |
| Hợp với | Một lời gọi, workflow bạn kiểm soát từng bước | Agent cần đọc file, chạy lệnh, làm nhiều bước |

Điều cần biết trước khi dùng (docs Agent SDK, kiểm 25/11/2026):

- Gói Python: `claude-agent-sdk`, bản mới nhất 0.2.189 (25/11/2026), cần Python 3.10 trở lên. Gói kèm sẵn Claude Code CLI (bản 0.2.189 kèm CLI 2.1.332), nên không cần cài Node.
- Xác thực bằng `ANTHROPIC_API_KEY`. SDK **không** tự đọc file `.env` (`claude_vi` nạp `.env` vào biến môi trường giúp bạn). Nhà cung cấp đám mây bật bằng biến môi trường: Amazon Bedrock (`CLAUDE_CODE_USE_BEDROCK=1`), Google Cloud's Agent Platform (`CLAUDE_CODE_USE_VERTEX=1`), Microsoft Foundry (`CLAUDE_CODE_USE_FOUNDRY=1`), Claude Platform on AWS.
- Sản phẩm của bên thứ ba **không** được cho người dùng đăng nhập bằng tài khoản claude.ai hay dùng hạn mức claude.ai, trừ khi Anthropic đã duyệt. Dùng API key. Việc dùng SDK theo Commercial Terms của Anthropic.
- Đặt tên sản phẩm: "Claude Agent" hay "<Tên bạn> Powered by Claude" thì được; "Claude Code" hay giao diện giống Claude Code thì không.
- Docs của Agent SDK đã chuyển từ `platform.claude.com/docs/en/agent-sdk/` sang `code.claude.com/docs/en/agent-sdk/` (đường cũ chuyển hướng sang đường mới).

## 2. `query()` và luồng message

```python
async for msg in sdk.query(prompt="Chiều nay máy HV-200 còn trống không?", options=options):
    if isinstance(msg, sdk.ResultMessage):
        print(msg.subtype, msg.num_turns, msg.total_cost_usd, msg.result)
```

`query()` trả một async iterator. Mỗi lần gọi là một **phiên mới**, trừ khi bạn `resume` (mục 6). Muốn hội thoại nhiều lượt trong một process, có ngắt giữa chừng, thì dùng `ClaudeSDKClient` (repo chưa có mock cho lớp này).

Các loại message:

| Message | Nội dung chính |
|---|---|
| `SystemMessage`, `subtype="init"` | `data` có `session_id`, `model`, `tools`, `mcp_servers`, `permissionMode` |
| `AssistantMessage` | `content`: `TextBlock`, `ThinkingBlock`, `ToolUseBlock`. **Mỗi message mang một block**; các block của cùng một response có chung `message_id` |
| `UserMessage` | `ToolResultBlock`: kết quả tool SDK gửi lại cho Claude |
| `ResultMessage` | `subtype`, `is_error`, `num_turns`, `session_id`, `total_cost_usd`, `usage`, `result`, `permission_denials` |

`ResultMessage.subtype` có 5 giá trị: `success`, `error_during_execution`, `error_max_turns`, `error_max_budget_usd`, `error_max_structured_output_retries`. `result` chỉ có khi `success`. `success` vẫn có thể đi kèm `is_error=True`: model từ chối (`stop_reason="refusal"`), tool hoãn không còn dùng được, hoặc request cuối lỗi API (xem `terminal_reason`, `api_error_status`). Kiểm cả hai.

`permission_denials` liệt kê lời gọi bị từ chối. Mock ghi cả lời gọi bị hook chặn; SDK thật có ghi trường hợp này không thì repo chưa kiểm, nên bài 1 đếm lỗi bằng `ToolResultBlock.is_error`.

**Đọc hết luồng.** Đừng `break` khi gặp `ResultMessage`: vài message hệ thống có thể tới sau nó.

## 3. System prompt, settings và tool dựng sẵn

Ba mặc định dễ làm bạn bất ngờ:

- **System prompt mặc định là bản tối giản**, không phải system prompt của Claude Code (và không có các hướng dẫn an toàn của preset `claude_code`). Muốn hành vi của Claude Code: `system_prompt={"type": "preset", "preset": "claude_code", "append": "..."}`.
- **`setting_sources` mặc định nạp mọi nguồn settings** (user, project, local), gồm cả `CLAUDE.md` của dự án và của `~/.claude`. Agent của bạn có thể làm theo chỉ dẫn trong file của máy bạn. `setting_sources=[]` bỏ ba nguồn này, nhưng **không** cách ly hoàn toàn: policy do quản trị viên đặt, `~/.claude.json` và auto memory (`~/.claude/projects/<dự án>/memory/`) vẫn được nạp. Trong container nhiều khách hàng, docs khuyên: mỗi khách một filesystem, `setting_sources=[]` và biến môi trường `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- **Tool dựng sẵn bật sẵn.** `tools=[]` tắt hết; `tools=["Read", "Grep"]` chỉ bật vài tool. Tên tool dựng sẵn (dùng trong luật quyền và hook): `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `Agent` (tên cũ `Task`), và nhiều tool khác. Trên Linux, macOS và WSL, `Glob` và `Grep` mặc định không có (Claude tìm bằng `find`/`grep` qua `Bash`). Chúng quay lại khi bạn ghi tên trong `tools` hoặc `allowed_tools` (một tên trong `allowed_tools` trả lại cả hai), hoặc khi bỏ `Bash` (ví dụ `disallowed_tools=["Bash"]`).

`options_co_ban()` trong `cong_cu.py` đặt `tools=[]`, `setting_sources=[]`, `max_turns=5`, `max_budget_usd=0.01` vì vậy.

## 4. Tool tự viết

```python
@sdk.tool("tra_lich", "Tra lịch đặt trước của một thiết bị.", {
    "type": "object",
    "properties": {"ma_thiet_bi": {"type": "string", "enum": ["HV-200", "LN-1200", "QS-3"]}},
    "required": ["ma_thiet_bi"],
})
async def tra_lich(args):
    return {"content": [{"type": "text", "text": "HV-200: chiều trống."}]}

server = sdk.create_sdk_mcp_server(name="phong-thi-nghiem", version="1.0.0", tools=[tra_lich])
options = sdk.ClaudeAgentOptions(mcp_servers={"ptn": server}, allowed_tools=["mcp__ptn__tra_lich"])
```

- `input_schema` có ba dạng: dạng đơn giản `{"ma_thiet_bi": str}` (mọi khoá bắt buộc), JSON Schema đầy đủ, hoặc lớp `TypedDict`. Cần `enum`, trường không bắt buộc hay khoảng giá trị thì dùng JSON Schema.
- SDK kiểm input theo `input_schema` **trước** khi gọi handler. Input sai schema (thiếu trường, sai kiểu, ngoài `enum`) trả `Input validation error` cho Claude, handler không chạy. Lỗi trong handler dành cho điều schema không diễn tả được (giá trị chỉ biết lúc chạy).
- Handler là hàm async nhận **một** dict. Nó trả `{"content": [...]}`, thêm `"is_error": True` khi lỗi. Exception trong handler cũng thành kết quả lỗi gửi cho Claude. Viết lời nhắn lỗi có ích như module 08: sai gì, giá trị nào hợp lệ.
- Tên đầy đủ là `mcp__<khoá trong mcp_servers>__<tên tool>`. Khoá là `"ptn"`, không phải `name` của `create_sdk_mcp_server`.
- Server chạy **trong process** của bạn, không cần process riêng.

## 5. Ai được chạy tool nào

Khi Claude muốn gọi một tool, SDK xét theo thứ tự (docs Permissions):

1. **Hook** `PreToolUse`: có thể cho phép, từ chối, hoặc không ý kiến.
2. **Luật deny** (`disallowed_tools`): thắng mọi thứ, kể cả `bypassPermissions` và kể cả khi hook đã cho phép.
3. **Luật ask**.
4. **`permission_mode`**: `default`, `acceptEdits`, `plan`, `bypassPermissions`, `dontAsk`, `auto`.
5. **Luật allow** (`allowed_tools`).
6. **`can_use_tool`**: callback của bạn. Ở `dontAsk` bước này bị bỏ và lời gọi bị từ chối.

Những điều suy ra:

- **`allowed_tools` là danh sách duyệt sẵn, không phải danh sách giới hạn.** Tool không có trong đó vẫn tồn tại và đi tiếp xuống `permission_mode` và `can_use_tool`. Muốn bỏ hẳn một tool: tên trần trong `disallowed_tools` hoặc không đưa vào `tools`.
- Glob trong luật: `mcp__ptn__*` duyệt mọi tool của một server; `*` hay `mcp__*` trong `allowed_tools` bị **bỏ qua**. Trong `disallowed_tools` thì `*` chặn mọi tool, `mcp__*` chặn mọi tool MCP.
- **Lời gọi đã được duyệt ở bước trước thì không tới `can_use_tool`.** Muốn soi mọi lời gọi, dùng hook `PreToolUse`. SDK cảnh báo khi bạn đăng ký `can_use_tool` cùng `allowed_tools` hoặc `bypassPermissions`.
- Agent chạy không người canh: dùng `allowed_tools` kèm `permission_mode="dontAsk"`. Trong mode mặc định (Claude Code từ 2.1.302), lời gọi cần duyệt mà không ai duyệt thì bị từ chối.
- **`bypassPermissions`** cho Claude toàn quyền trên máy. Ở mode này `allowed_tools` không giới hạn gì cả. Subagent cũng thừa hưởng mode này.

`can_use_tool` (script 02, bài 2):

```python
async def can_use_tool(tool_name, input_data, context):
    if tool_name == "mcp__ptn__ghi_nhat_ky" and len(input_data["noi_dung"]) <= 200:
        return sdk.PermissionResultAllow(updated_input={"noi_dung": "[agent] " + input_data["noi_dung"]})
    return sdk.PermissionResultDeny(message="Không duyệt: nội dung quá dài.")
```

Hook (script 02, bài 2):

```python
async def chan_xoa(input_data, tool_use_id, context):
    if "xoá" in str(input_data["tool_input"]).lower():
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": "Nhật ký chỉ được thêm."}}
    return {}   # không ý kiến

hooks = {"PreToolUse": [sdk.HookMatcher(matcher="^mcp__ptn__", hooks=[chan_xoa])]}
```

- `matcher` chỉ so với **tên** tool, không so với tham số. Matcher chỉ gồm chữ, số, `_` và `|` là tên chính xác (`"mcp__ptn__ghi_nhat_ky"`, hay danh sách `"Write|Edit"`); còn lại là regex (`"^mcp__ptn__"`). `"ghi_nhat_ky"` **không** khớp `mcp__ptn__ghi_nhat_ky`. Lọc theo nội dung phải làm trong callback.
- Python có 10 sự kiện hook: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `PreCompact`, `Notification`, `SubagentStart`, `PermissionRequest`. `SessionStart` và `SessionEnd` không có ở Python.
- Callback lỗi (ném exception) thì mặc định lời gọi đi tiếp như không có hook: **mở cửa khi lỗi**. Đặt `on_failure="block"` trong `HookMatcher` để chặn khi hook hỏng; khi đó callback trả `None` cũng tính là hỏng, nên muốn "không ý kiến" thì trả `{}`.
- `additionalContext` trong `hookSpecificOutput` tới được Claude; `systemMessage` chỉ hiện cho người dùng.
- Hook cho `Write|Edit` không bắt được việc ghi file qua `Bash`.

## 6. Giới hạn, lỗi và phiên

- `max_turns` và `max_budget_usd` mặc định **không giới hạn**. Mỗi lượt có gọi tool tính một lượt, dù trong lượt đó Claude gọi một hay nhiều tool song song; câu trả lời cuối thêm một lượt.
- `max_budget_usd` dựa trên ước tính chi phí phía client, kiểm **sau** mỗi response, nên có thể vượt trần một chút. Nó chỉ tính chi phí của lần gọi này, không tính phần cũ của phiên resume.
- Chạm giới hạn: `ResultMessage` có `subtype` `error_max_turns` hoặc `error_max_budget_usd`, rồi `query()` ném `ResultError` (từ SDK 0.2.140). **Mọi** result lỗi đều vậy, kể cả `subtype="success"` kèm `is_error=True`. Vì thế luôn bọc vòng `async for` trong `try` như `doc_het()` trong `cong_cu.py`. `ResultError` có `subtype`, `errors`, `session_id`, `data`; docs khuyên phân loại theo `data["stop_reason"]`, rồi `terminal_reason`, rồi `subtype`.
- **Phiên.** `session_id` có trong `SystemMessage` init và trong `ResultMessage`. `resume=<id>` nối tiếp phiên đó; thêm `fork_session=True` để rẽ sang id mới, phiên gốc giữ nguyên. `continue_conversation=True` nối phiên gần nhất trong thư mục, không dùng chung với `resume`. Phiên lưu thành file JSONL trên máy (`~/.claude/projects/...`): máy khác muốn resume thì dùng `session_store`, hoặc chép file JSONL của phiên sang `~/.claude/projects/` của máy đó.

## 7. Chi phí

- `ResultMessage.total_cost_usd` là **ước tính phía client**, không phải hoá đơn. Đừng tính tiền người dùng theo số này.
- `usage` của `ResultMessage` chỉ gồm vòng lặp chính; `total_cost_usd` và `model_usage` gồm cả subagent. Các trường này là `Optional`: kiểm `None`.
- Phiên resume: `total_cost_usd` **đã gồm** chi phí các lần trước. Cộng kết quả của hai lần chạy cùng phiên là tính trùng (script 03, phần 4).
- Đếm theo từng bước bằng `AssistantMessage.usage` thì khử trùng theo `message_id`: các block của cùng một response (ví dụ nhiều tool gọi song song) có chung id. Số input và cache theo bước thì dùng được; `output_tokens` theo bước chỉ là giá trị giữ chỗ, đọc tổng output từ `ResultMessage.usage`.
- Mỗi `query()` chạy một process CLI. Docs gợi ý bắt đầu với 1 GiB RAM, 5 GiB đĩa và 1 CPU cho mỗi agent khi đóng container.

## 8. Vài tính năng khác (chỉ giới thiệu)

- **Subagent:** `agents={"ten": sdk.AgentDefinition(description=..., prompt=..., tools=[...], model="haiku")}`. Claude giao việc qua tool `Agent`. Subagent (trừ fork) bắt đầu **không có hội thoại** của agent chính; context của nó không trống (system prompt, tool, `CLAUDE.md` của nó), nhưng thứ duy nhất truyền sang là chuỗi prompt của tool `Agent`. Nó chỉ trả về message cuối. Chi phí của nó tính vào `total_cost_usd`. Trường nhiều chữ của `AgentDefinition` viết kiểu camelCase (`disallowedTools`, `maxTurns`).
- **Structured outputs:** `output_format={"type": "json_schema", "schema": {...}}`, đọc `ResultMessage.structured_output`. `success` chưa chắc có output: kiểm `is_error` và trường này.
- **Thinking và effort:** `effort="low"` tới `"max"`; `thinking={"type": "adaptive", "display": "summarized"}` để đọc tóm tắt suy nghĩ. `max_thinking_tokens` đã lỗi thời.
- **An toàn:** docs nêu hai nguồn gây hành động ngoài ý muốn: prompt injection và lỗi của model. Dùng nhiều lớp bảo vệ: quyền tối thiểu, sandbox, đưa credential qua proxy thay vì cho agent đọc.

## Bẫy thường gặp

- **Tưởng `allowed_tools` là danh sách giới hạn.** Nó chỉ duyệt sẵn. Dùng `tools`/`disallowed_tools` để bỏ tool.
- **Tưởng `can_use_tool` soi mọi lời gọi.** Lời gọi đã được duyệt không tới đó. Dùng hook `PreToolUse`.
- **Không đặt `max_turns`, `max_budget_usd`.** Mặc định không giới hạn.
- **Để agent nạp `CLAUDE.md` và settings của máy.** Đặt `setting_sources=[]` khi không cần, và nhớ nó không cách ly hoàn toàn (mục 3).
- **Viết tên tool sai.** Đúng là `mcp__<khoá trong mcp_servers>__<tool>`. `mcp__*` trong `allowed_tools` không duyệt gì.
- **Lọc theo tham số bằng `matcher`, hoặc viết matcher là một phần tên.** `matcher` chỉ so tên tool; chuỗi chỉ có chữ, số và `_` là tên chính xác.
- **Hook ném exception rồi tưởng đã chặn.** Mặc định là mở cửa; dùng `on_failure="block"`.
- **`break` khỏi luồng ngay ở `ResultMessage`**, hoặc tưởng một `AssistantMessage` chứa cả response.
- **Cộng `total_cost_usd` của các lần resume cùng phiên.** Số sau đã gồm số trước.
- **Coi `total_cost_usd` là hoá đơn.** Nó là ước tính.
- **Dùng `bypassPermissions` cho tiện.** Claude có toàn quyền trên máy, kể cả subagent.

## Điều gì đã thay đổi ở model 5.x

| Trước đây | Bây giờ |
|---|---|
| Claude Code SDK, `ClaudeCodeOptions` | Claude Agent SDK, `ClaudeAgentOptions` (đổi tên từ bản 0.1.0) |
| Giới hạn suy nghĩ bằng `max_thinking_tokens` | `effort` và `thinking` (adaptive); `max_thinking_tokens` lỗi thời. Trên model 5.x đừng dùng `{"type": "enabled", "budget_tokens": ...}` (module 07) |
| Tool giao việc cho subagent tên `Task` | Tên `Agent`; `Task` vẫn được nhận, và danh sách tool trong init vẫn ghi `Task` |
| Tóm tắt thinking hiện mặc định | Từ Opus 4.7, `display` mặc định là `"omitted"`: muốn đọc `ThinkingBlock` thì đặt `"summarized"` |
| Số token đếm ở model cũ | Model từ 4.7 dùng tokenizer mới, cùng text cho khoảng 30% token nhiều hơn (module 06): chi phí agent đo lại trên model mới |

## Bài tập

| Bài | Việc | Chấm |
|---|---|---|
| [`bai1_doc_ket_qua.py`](exercises/bai1_doc_ket_qua.py) | Tóm tắt một lần chạy từ luồng message: tool đã gọi, tool lỗi, số lượt, chi phí, thành công hay không | lần chạy thành công, lần chạm `max_turns`, `success` kèm `is_error` |
| [`bai2_quyen.py`](exercises/bai2_quyen.py) | `can_use_tool` có `updated_input`, hook `PreToolUse` chặn theo nội dung | từng trường hợp duyệt/từ chối, chạy cùng agent mock |
| [`bai3_tuy_chon.py`](exercises/bai3_tuy_chon.py) | Một tool tự viết có `enum` và lỗi có ích; options cho agent không người canh (`dontAsk`) | đổi nhiệt độ đúng, đơn vị sai thì `is_error`, options đúng từng trường |

```bash
CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q   # chấm bài của bạn
CLAUDE_MOCK=1 uv run pytest modules/09-agent-sdk -q                  # chấm lời giải
```

Câu hỏi ôn tập: [quiz.md](quiz.md).

## Tiếp theo

Module 10 (MCP) đi sâu vào server MCP: bạn đã dùng một server chạy trong process ở mục 4. Nguồn của module này: [references.md](references.md).
