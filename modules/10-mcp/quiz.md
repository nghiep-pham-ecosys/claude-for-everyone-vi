# Quiz · Module 10

**1.** Trong MCP, ai xin người dùng đồng ý trước khi một tool được gọi?

- A. Server
- B. Host (ứng dụng có LLM)
- C. Không ai, tool tự chạy

<details><summary>Đáp án</summary>

**B.** Host quản lý client, giữ luật an toàn và xin người dùng đồng ý. Theo nguyên tắc thiết kế, server không nên thấy cả hội thoại.
</details>

**2.** Server stdio của bạn có một lệnh `print("debug")`. Chuyện gì xảy ra?

- A. Không sao, client bỏ qua
- B. Có thể làm hỏng kết nối: stdout chỉ dành cho message MCP; log phải ra stderr
- C. Dòng đó hiện cho người dùng

<details><summary>Đáp án</summary>

**B.** Mỗi dòng trên stdout phải là một message JSON-RPC.
</details>

**3.** Ai điều khiển từng primitive phía server?

- A. Tool: người dùng; resource: model; prompt: ứng dụng
- B. Tool: model; resource: ứng dụng; prompt: người dùng
- C. Cả ba do model điều khiển

<details><summary>Đáp án</summary>

**B.** Claude chọn khi nào gọi tool; host quyết định đưa resource nào vào context; người dùng chọn prompt như một lệnh tắt.
</details>

**4.** Một server khai tool `don_dep` có `read_only_hint=True`. Host có nên chạy nó mà không hỏi?

- A. Có, server đã khai là chỉ đọc
- B. Không: annotation chỉ là gợi ý, không đáng tin nếu server không đáng tin; host tự giữ danh sách tool được chạy không cần hỏi
- C. Chỉ khi `idempotent_hint=True`

<details><summary>Đáp án</summary>

**B.** Luật của module: với server chưa được tin, annotation chỉ được làm host thận trọng hơn (ví dụ `destructive_hint=True` thì luôn hỏi). Spec cho phép tin annotation khi server đáng tin.
</details>

**5.** Trong tool của `MCPServer` (SDK 2.x), bạn `raise ValueError("thiếu mã mẫu")`. Model thấy gì?

- A. `thiếu mã mẫu`
- B. Chỉ `Error executing tool <tên>`; lời nhắn gốc nằm ở log của server. Muốn model đọc được thì `raise ToolError(...)`
- C. Không thấy gì, kết nối đứt

<details><summary>Đáp án</summary>

**B.** `ToolError` là lỗi đã lường trước: client nhận `is_error=True` kèm lời nhắn. Exception khác (trừ `MCPError`) bị coi là crash. Script 02 cho thấy cả hai.
</details>

**6.** Spec MCP 2026-07-28 khác 2025-11-25 ở điểm lớn nào?

- A. Bỏ JSON-RPC
- B. Bỏ handshake `initialize`: mỗi request tự mang phiên bản giao thức và capability của client
- C. Chỉ còn transport stdio

<details><summary>Đáp án</summary>

**B.** Server không được dựa vào request trước đó. Session ở Streamable HTTP cũng bị bỏ.
</details>

**7.** Code mẫu trên mạng viết `from mcp.server.fastmcp import FastMCP`. Với `mcp` 2.3.0 nó chạy không?

- A. Có
- B. Không: SDK 2.x đổi `FastMCP` thành `MCPServer` (`mcp.server.mcpserver`) và đổi thuộc tính sang `snake_case`
- C. Chỉ chạy trên Python 3.10

<details><summary>Đáp án</summary>

**B.** Import cũ báo `ModuleNotFoundError` kèm link hướng dẫn chuyển đổi.
</details>

**8.** Bạn muốn Claude (qua Messages API) dùng một MCP server chạy bằng stdio trên laptop. MCP connector có làm được không?

- A. Có, chỉ cần khai `command`
- B. Không: connector chỉ nối server từ xa qua HTTPS; server stdio thì host tự làm cầu (script 03) hoặc dùng Agent SDK / Claude Code
- C. Có, nhưng chỉ với resource

<details><summary>Đáp án</summary>

**B.** Connector cũng chỉ hỗ trợ tool, không hỗ trợ resource và prompt.
</details>

**9.** Khi đổi `CallToolResult` sang `tool_result`, bạn quên chép `is_error`. Hậu quả?

- A. Không sao
- B. Claude tưởng tool chạy thành công và có thể trả lời dựa trên một lời nhắn lỗi
- C. API trả 400

<details><summary>Đáp án</summary>

**B.** Giữ `is_error` để Claude biết cần sửa tham số hay thử cách khác.
</details>

**10.** Tool MCP tên `lich.tra` (hợp lệ theo spec MCP). Gửi thẳng tên đó trong `tools` của Messages API được không?

- A. Được
- B. Không: tên tool của Messages API chỉ nhận chữ, số, `_` và `-`; host phải đổi tên và giữ bảng tra ngược
- C. Được nếu thêm tiền tố `mcp__`

<details><summary>Đáp án</summary>

**B.** Bài 2 làm đúng việc này: thêm tiền tố server, thay ký tự không hợp lệ, cắt còn 128 ký tự.
</details>
