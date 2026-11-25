# 10 · MCP (Model Context Protocol)

**Loại:** Learn + Build · **Thời lượng:** khoảng 2 giờ · **Cần:** module 03, 08 và 09 · **Chi phí:** $0. Server và client MCP chạy trên máy, không gọi API. Chỉ script 03 gọi Claude: $0 ở mock mode, dưới $0,01 nếu chạy thật với `claude-haiku-5-5` (xem [references.md](references.md))

## Mục tiêu

Sau module này bạn:

- Biết MCP là gì và ai làm gì: host, client, server.
- Phân biệt ba thứ một server cung cấp: tool, resource, prompt, và ai điều khiển từng thứ.
- Viết được một MCP server nhỏ bằng SDK Python chính thức (`mcp` 2.x) và chạy nó qua stdio.
- Viết được client gọi tool, đọc resource, lấy prompt, và đọc đúng kết quả (`content`, `structured_content`, `is_error`).
- Nối tool MCP với Claude trong vai host, và tự giữ luật duyệt thay vì tin annotation của server.
- Biết ba cách khác để dùng MCP với Claude: MCP connector của Messages API, Agent SDK, Claude Code.

| Learn | Build |
|---|---|
| Đọc mục 1–8, chạy 3 script trong `python/` | Làm 3 bài trong `exercises/`, chấm bằng test |

## Vì sao học cái này

Ở module 03, 08 và 09, tool nằm ngay trong code của bạn. Muốn dùng lại cùng một bộ tool cho nhiều ứng dụng (Claude Code, Claude Desktop, agent của bạn, ứng dụng của người khác) thì mỗi nơi phải viết lại phần nối. **MCP** là một giao thức mở chuẩn hoá phần đó: viết server một lần, mọi host hiểu MCP đều dùng được.

Đổi lại, tool đến từ **người khác**. Mô tả tool là chữ mà model đọc, nên một server lạ có thể lái model. Module này dạy cả cách dùng lẫn cách giữ quyền kiểm soát.

## Tối thiểu chạy được

```bash
uv run python modules/10-mcp/python/01_kham_pha_may_chu.py
```

| File | Ý chính |
|---|---|
| [`may_chu_ptn.py`](python/may_chu_ptn.py) | MCP server: tool `tra_lich`, `xem_mau` (chỉ đọc), `ghi_nhat_ky` (có tác dụng phụ), resource `ptn://so-tay`, prompt `hoi_lich` |
| [`01_kham_pha_may_chu.py`](python/01_kham_pha_may_chu.py) | Client khởi động server qua stdio, xem phiên bản giao thức, tool, resource, prompt |
| [`02_goi_tool.py`](python/02_goi_tool.py) | Gọi tool, đọc kết quả có cấu trúc, các kiểu lỗi, đọc resource, lấy prompt |
| [`03_claude_dung_mcp.py`](python/03_claude_dung_mcp.py) | Host nối tool MCP với Claude (`ClaudeVi`, mock mode), duyệt tool có tác dụng phụ |
| [`cau_noi.py`](python/cau_noi.py) | Phần dùng chung: tham số stdio, đổi tool MCP sang tool của Messages API, đổi kết quả sang `tool_result`, luật duyệt |

Server và client ở đây là **thật**: SDK `mcp` 2.3.0 đã nằm trong dependency của repo, mọi thứ chạy trên máy, không cần mạng hay API key. Chỉ phần Claude của script 03 dùng mock (`CLAUDE_MOCK=1`). Các dòng bắt đầu bằng `Tool ...` khi chạy script 02 là log của server ghi ra stderr: đúng luật stdio ở mục 1.

## 1. Host, client, server

| Vai | Là gì | Trong module này |
|---|---|---|
| **Host** | Ứng dụng có LLM: quản lý client, xin người dùng đồng ý, nối với model | Script 03 |
| **Client** | Một kết nối tới **một** server, nằm trong host | `mcp.Client` |
| **Server** | Chương trình cung cấp tool, resource, prompt | `may_chu_ptn.py` |

Một host có nhiều client, mỗi client nói chuyện với đúng một server. Theo nguyên tắc thiết kế, server không nên thấy cả hội thoại hay các server khác; host là bên giữ ranh giới này (ví dụ: đừng nhét cả hội thoại vào tham số tool).

MCP có hai lớp:

- **Lớp dữ liệu:** message JSON-RPC 2.0, một định dạng JSON chuẩn cho request và response; mỗi request có `id` để ghép với response, còn notification là tin một chiều không cần trả lời.
- **Lớp vận chuyển (transport):** **stdio** (host chạy server như process con, mỗi message một dòng trên stdin/stdout) hoặc **Streamable HTTP** (server từ xa, mỗi message một request POST). Transport HTTP+SSE cũ đã lỗi thời.

Luật của stdio: server **chỉ** được ghi message MCP ra stdout; log ghi ra stderr. Một lệnh `print()` lạc trong server là đủ làm hỏng kết nối. Vì vậy `may_chu_ptn.py` chỉ chạy làm server khi có cờ `--stdio`.

## 2. Phiên bản giao thức: 2026-07-28

Vì sao cần biết: phần lớn code mẫu và bài viết trên mạng vẫn theo phiên bản 2025-11-25, nên bạn sẽ gặp các khái niệm cũ. Phiên bản hiện tại của spec là **2026-07-28** (tên phiên bản là ngày của thay đổi không tương thích gần nhất). So với 2025-11-25, nó đổi nhiều:

- **Không còn handshake** (bước chào hỏi đầu kết nối). Trước đây, mọi kết nối bắt đầu bằng `initialize`. Bây giờ mỗi request tự mang phiên bản giao thức và capability (danh sách tính năng mà client hỗ trợ) trong `_meta`; server không được dựa vào request trước đó. Có thêm request `server/discover` để hỏi server hỗ trợ gì (client có thể bỏ qua).
- **Không còn session** ở Streamable HTTP. Tool cần giữ trạng thái thì nhận một "handle" rõ ràng trong tham số.
- Server không còn tự gửi request cho client; thay bằng **Multi Round-Trip Requests**: server trả `InputRequiredResult`, client gửi lại request kèm câu trả lời.
- **Lỗi thời:** sampling, roots và logging. Phía client chỉ còn elicitation (xin người dùng nhập thông tin) là chưa lỗi thời.

`mcp.Client` của SDK Python mặc định (`mode="auto"`) thử `server/discover` trước; server cũ thì quay về `initialize`. Script 01 in ra phiên bản đã thống nhất: `2026-07-28`.

## 3. Ba thứ một server cung cấp

| Primitive | Ai điều khiển | Ví dụ |
|---|---|---|
| **Tool** | Model: Claude chọn khi nào gọi | `tra_lich`, `ghi_nhat_ky` |
| **Resource** | Ứng dụng: host quyết định đưa gì vào context | `ptn://so-tay` |
| **Prompt** | Người dùng: chọn như một lệnh tắt | `hoi_lich` |

Tool là phần dùng nhiều nhất. Mỗi tool có:

- `name`: spec khuyến nghị (SHOULD) 1–128 ký tự `A-Z a-z 0-9 _ - .`, không trùng trong một server. Vì chỉ là khuyến nghị, host vẫn phải chịu được tên sai luật. Messages API không nhận dấu `.` trong tên tool (bài 2).
- `description`: model đọc nó để quyết định gọi tool. Đây cũng là chỗ một server xấu có thể chèn chỉ dẫn (mục 6).
- `inputSchema`: JSON Schema của tham số.
- `outputSchema` (tuỳ chọn): khi có, kết quả mang `structuredContent` đúng schema đó, và nên kèm bản JSON dạng text cho client cũ.
- `annotations`: `readOnlyHint` (mặc định false), `destructiveHint` (mặc định true, chỉ có nghĩa khi `readOnlyHint` là false), `idempotentHint` (mặc định false), `openWorldHint` (mặc định true). Server không khai thì thuộc tính Python là `None`. **Chỉ là gợi ý**: spec bảo client không tin chúng nếu server không đáng tin.

## 4. Viết server bằng SDK Python 2.x

```python
from typing import Literal, TypedDict
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

server = MCPServer("phong-thi-nghiem", version="1.0.0")

class LichThietBi(TypedDict):
    ma_thiet_bi: str
    lich: str

@server.tool(annotations=ToolAnnotations(read_only_hint=True))
def tra_lich(ma_thiet_bi: Literal["HV-200", "LN-1200", "QS-3"]) -> LichThietBi:
    """Tra lịch đặt trước của một thiết bị phòng thí nghiệm."""
    return {"ma_thiet_bi": ma_thiet_bi, "lich": LICH[ma_thiet_bi]}

server.run()   # mặc định stdio
```

- Tên tool lấy từ tên hàm, mô tả lấy từ docstring, `inputSchema` lấy từ type hint. `Literal` thành `enum`. Tham số không có giá trị mặc định là bắt buộc.
- Kiểu trả về thành `outputSchema`. `TypedDict`, model Pydantic, dataclass, `dict[str, ...]` cho `structured_content` dạng object. `str`, `int`... được bọc thành `{"result": ...}`.
- Tham số sai schema bị chặn **trước** khi hàm chạy.
- **Lỗi:** `raise ToolError("...")` cho lỗi đã lường trước: client nhận `is_error=True` kèm lời nhắn (có tiền tố `Error executing tool <tên>:`). Exception khác (trừ `MCPError`, thành lỗi JSON-RPC) bị coi là crash: model chỉ thấy `Error executing tool <tên>`, lời nhắn gốc nằm lại ở log của server. Script 02 cho thấy cả hai: `ghi_nhat_ky` dùng `ToolError`, `xem_mau` với mã lạ thì crash.
- Phiên bản 2 đổi nhiều so với 1.x: `FastMCP` đổi tên thành `MCPServer` (`mcp.server.mcpserver`); thuộc tính của các kiểu dữ liệu viết `snake_case` trong Python (`input_schema`, `is_error`, `structured_content`) dù JSON trên đường truyền vẫn là `camelCase`. Code và bài viết cho 1.x trên mạng không chạy nguyên văn với 2.x.

## 5. Viết client

```python
from mcp import Client, StdioServerParameters

thong_so = StdioServerParameters(command=sys.executable, args=["may_chu_ptn.py", "--stdio"])
async with Client(thong_so) as mcp:
    print(mcp.protocol_version, mcp.server_info)
    tools = (await mcp.list_tools()).tools
    kq = await mcp.call_tool("tra_lich", {"ma_thiet_bi": "HV-200"})
    print(kq.is_error, kq.structured_content, kq.content)
```

- `Client(...)` nhận một URL (Streamable HTTP), một `StdioServerParameters` (khởi động process con), một transport tự viết, hoặc chính object server (nối trong process, dùng cho test: `Client(server)`). Bài tập và test của module dùng cách cuối.
- `Client` là async context manager: vào thì kết nối, ra thì đóng. Không dùng lại được sau khi ra. Các script đặt `read_timeout_seconds=30` để không treo mãi nếu server hỏng.
- Server stdio **không** thừa hưởng mọi biến môi trường của bạn: SDK chỉ chuyển vài biến an toàn (`HOME`, `PATH`...) cộng những gì bạn đưa vào `StdioServerParameters(env={...})`. Host quyết định server thấy gì. Trong Claude Code, tương đương là `claude mcp add --env KEY=value`.
- Kết quả `call_tool`: `content` (block cho model đọc), `structured_content` (dữ liệu cho code), `is_error`.
- **Hai loại lỗi theo spec:** lỗi khi chạy tool trả trong kết quả với `isError: true`, để model đọc và tự sửa; lỗi giao thức (request sai, tool không tồn tại theo spec) là lỗi JSON-RPC. SDK Python 2.3.0 trả cả tool lạ về dạng `is_error=True`; `Client` chỉ ném `MCPError` khi server trả lỗi JSON-RPC.

## 6. Nối MCP với Claude: host làm cầu

Messages API không tự nói chuyện với server chạy trên máy bạn. Host làm cầu (script 03):

1. `list_tools` trên server, đổi mỗi tool thành `{"name", "description", "input_schema"}` của Messages API.
2. Gửi cho Claude; Claude trả `tool_use`.
3. **Host duyệt**, rồi `call_tool` trên server.
4. Đổi `CallToolResult` thành block `tool_result` (giữ `is_error`), gửi lại. Lặp như vòng lặp agent của module 08.

Luật duyệt nằm ở **host**, không ở server:

- Spec (trang Tools): NÊN (SHOULD) luôn có người có thể từ chối một lời gọi tool, và client NÊN hỏi xác nhận với thao tác nhạy cảm; trang tổng quan nêu nguyên tắc host xin đồng ý trước khi gọi tool. `CHAY_KHONG_HOI` trong `cau_noi.py` là sự đồng ý người dùng cho **trước** với vài tool chỉ đọc: do host hoặc người dùng đặt, không bao giờ do server. Mọi tool khác được hỏi ở từng lời gọi.
- `read_only_hint=True` là lời **server tự khai**. Một server xấu có thể khai tool xoá dữ liệu là "chỉ đọc". Host giữ danh sách riêng các tool được chạy không cần hỏi. Luật của module: với server chưa được tin, annotation chỉ được dùng để **thận trọng hơn** (bài 3). Spec cho phép tin annotation khi server đáng tin.
- Kết quả tool và mô tả tool là **dữ liệu không đáng tin**, như module 08 mục 6. Docs của MCP cảnh báo về "tool poisoning" (mô tả tool chứa chỉ dẫn cho model) và mô tả đổi sau khi đã được duyệt.
- Server chạy qua stdio **không phải sandbox**: nó chạy với quyền của bạn. Chỉ cài server bạn tin, và xem đúng lệnh sẽ chạy trước khi cài.

SDK `anthropic` có sẵn helper cho việc này (`anthropic.lib.tools.mcp`, cài bằng extra `anthropic[mcp]`; `async_mcp_tool` dùng với tool runner). Module tự viết cầu nối để bạn thấy từng bước và đặt được luật duyệt của mình.

## 7. Ba cách khác để Claude dùng MCP

| Cách | Server | Hỗ trợ | Ghi chú |
|---|---|---|---|
| **MCP connector** của Messages API (beta) | Chỉ server từ xa, HTTPS (Streamable HTTP hoặc SSE); **không** stdio | Chỉ tool (không resource, prompt) | Khai `mcp_servers` (`type: "url"`, `url`, `name`, `authorization_token`) và một `{"type": "mcp_toolset", "mcp_server_name": ...}` trong `tools`. Header `mcp-client-2026-09-15` (mới hơn, gồm mọi thứ của bản 2025-11-20 và thêm ghim danh sách tool; Claude API, Google Cloud) hoặc `mcp-client-2025-11-20` (mọi nền tảng, gồm Claude Platform on AWS, Microsoft Foundry). Response có block `mcp_tool_use`, `mcp_tool_result`; với header 2026-09-15 có thêm `mcp_tool_listing`, phải gửi lại nguyên. Bạn tự lo OAuth. Không thuộc ZDR |
| **Agent SDK** (module 09) | stdio (`command`), HTTP/SSE (`url`), hoặc trong process (`create_sdk_mcp_server`) | Tool | Tên `mcp__<server>__<tool>`; cần cấp quyền rõ ràng, cách nên dùng là `allowed_tools` (ví dụ `mcp__<server>__*`) |
| **Claude Code** | `claude mcp add --transport http <tên> <url>` hoặc `claude mcp add <tên> -- <lệnh>` | Tool, resource (`@`), prompt (lệnh `/`) | Phạm vi local, project (`.mcp.json`), user |

Muốn chặn tool ghi trong MCP connector: `default_config: {"enabled": false}` rồi bật từng tool chỉ đọc trong `configs`. Không có trường "allowlist" riêng.

## 8. An toàn khi dùng server của người khác

- **Tool poisoning:** mô tả tool chứa chỉ dẫn ẩn cho model. Đọc mô tả trước khi bật server; theo dõi khi nó đổi.
- **Prompt injection qua dữ liệu:** server trung thực vẫn có thể trả về nội dung do người khác viết (trang web, email). Giữ nó trong `tool_result`, đừng đưa vào `system`.
- **Không truyền token:** spec cấm server chuyển nguyên token của client sang API khác ("token passthrough").
- **Server cục bộ:** chạy với quyền của bạn. Ứng dụng cài server một chạm phải hiện đúng lệnh và xin đồng ý.
- **Server HTTP chạy trên máy:** bind vào `localhost`, kiểm header `Origin`, có xác thực.

## Bẫy thường gặp

- **In ra stdout trong server stdio.** Làm hỏng giao thức; log ra stderr.
- **Tin annotation của server** để bỏ bước duyệt. Host tự giữ danh sách.
- **Chép code của SDK 1.x** (`FastMCP`, `inputSchema` trong Python) vào SDK 2.x. `ClientSession` + `initialize()` vẫn còn ở 2.x như API mức thấp, nhưng `initialize()` ép handshake cũ (2025-11-25); dùng `mcp.Client`.
- **Tưởng server stdio thấy biến môi trường của bạn.** Truyền qua `env=`.
- **Ném exception thường trong tool** rồi tưởng model đọc được lời nhắn. Dùng `ToolError`.
- **Bỏ `is_error` khi đổi sang `tool_result`.** Claude sẽ tưởng tool chạy thành công.
- **Đặt dấu `.` trong tên tool** rồi gửi thẳng cho Messages API (tên tool ở đó chỉ nhận `[a-zA-Z0-9_-]`).
- **Dùng MCP connector cho server chạy trên máy.** Connector chỉ nối được server từ xa qua HTTPS.
- **Dựa vào sampling hoặc roots** cho thiết kế mới: đã lỗi thời từ 2026-07-28.

## Điều gì đã thay đổi ở model 5.x

MCP là giao thức, không gắn với một model. Những thay đổi liên quan tới module này:

| Trước đây | Bây giờ |
|---|---|
| Mỗi kết nối bắt đầu bằng `initialize` (spec 2025-11-25) | Spec 2026-07-28: không handshake, mỗi request tự mang phiên bản và capability |
| SDK Python 1.x: `FastMCP`; transport context manager + `ClientSession` + gọi tay `initialize()` | SDK 2.x (từ 28/07/2026): `MCPServer`; `mcp.Client` một lớp cho mọi transport |
| MCP connector: `tool_configuration` trong `mcp_servers` (header `mcp-client-2025-04-04`) | `mcp_toolset` trong `tools` (header `mcp-client-2025-11-20` hoặc `mcp-client-2026-09-15`); header cũ lỗi thời |
| Vòng lặp tool của host | Trên model 5.x vẫn theo luật của module 07: gửi lại nguyên lượt assistant, kể cả block thinking; script 03 làm vậy |

## Bài tập

| Bài | Việc | Chấm |
|---|---|---|
| [`bai1_may_chu.py`](exercises/bai1_may_chu.py) | Server đổi nhiệt độ: `Literal` thành `enum`, `TypedDict` thành `structured_content`, `ToolError`, annotation, một resource | gọi qua `Client(server)` trong process |
| [`bai2_cau_noi.py`](exercises/bai2_cau_noi.py) | Host nối nhiều server: tiền tố tên, sửa ký tự không hợp lệ, cắt 128 ký tự, bảng tra ngược | tên hợp lệ với Messages API, báo trùng |
| [`bai3_duyet.py`](exercises/bai3_duyet.py) | Luật duyệt không tin annotation; đổi `CallToolResult` sang `tool_result` | server tự khai "chỉ đọc" vẫn phải hỏi; giữ `is_error` |

```bash
CHAM=exercises CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q   # chấm bài của bạn
CLAUDE_MOCK=1 uv run pytest modules/10-mcp -q                  # chấm lời giải
```

Câu hỏi ôn tập: [quiz.md](quiz.md).

## Tiếp theo

Các module 11–15 (Claude Code, Agent Skills, Evals, Production, Research) mở cho cộng đồng đóng góp. Nguồn của module này: [references.md](references.md).
