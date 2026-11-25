# Quiz · Module 09

**1.** Khác biệt chính giữa Agent SDK và Client SDK (`anthropic`) là gì?

- A. Agent SDK rẻ hơn
- B. Agent SDK chạy vòng lặp tool và có tool dựng sẵn; với Client SDK bạn tự viết vòng lặp
- C. Agent SDK không cần API key

<details><summary>Đáp án</summary>

**B.** Agent SDK chạy Claude Code CLI như một process con và làm vòng lặp, chạy tool, quản lý context cho bạn. Vẫn cần API key.
</details>

**2.** Bạn đặt `allowed_tools=["mcp__ptn__tra_lich"]`. Claude có gọi được `Bash` không?

- A. Không bao giờ: chỉ tool trong `allowed_tools` mới tồn tại
- B. Có thể: `allowed_tools` chỉ duyệt sẵn; `Bash` vẫn tồn tại và đi tiếp tới `permission_mode` và `can_use_tool`
- C. Có, luôn chạy không cần duyệt

<details><summary>Đáp án</summary>

**B.** Muốn bỏ hẳn tool dựng sẵn: `tools=[]` hoặc tên trần trong `disallowed_tools`.
</details>

**3.** Bạn có `allowed_tools=["mcp__ptn__*"]` và một `can_use_tool` ghi log mọi lời gọi. Log trống. Vì sao?

- A. Lỗi của SDK
- B. Lời gọi đã được luật allow duyệt thì không tới `can_use_tool`; muốn soi mọi lời gọi thì dùng hook `PreToolUse`
- C. `can_use_tool` chỉ chạy với tool dựng sẵn

<details><summary>Đáp án</summary>

**B.** `can_use_tool` là bước cuối của luồng quyền.
</details>

**4.** Server tạo bằng `create_sdk_mcp_server(name="phong-thi-nghiem", tools=[tra_lich])`, đăng ký `mcp_servers={"ptn": server}`. Tên đầy đủ của tool là gì?

- A. `mcp__phong-thi-nghiem__tra_lich`
- B. `mcp__ptn__tra_lich`
- C. `tra_lich`

<details><summary>Đáp án</summary>

**B.** Phần giữa là khoá trong `mcp_servers`, không phải `name`.
</details>

**5.** Hook `PreToolUse` có `matcher="ghi_nhat_ky.*xoá"` để chặn lệnh xoá. Nó có chặn được không?

- A. Có
- B. Không: `matcher` chỉ so với tên tool; lọc theo tham số phải làm trong callback
- C. Có, nhưng chỉ ở `bypassPermissions`

<details><summary>Đáp án</summary>

**B.** Đặt `matcher` theo tên (ví dụ `"^mcp__ptn__"`), rồi kiểm `input_data["tool_input"]` trong callback.
</details>

**6.** `disallowed_tools=["Bash"]` cùng `permission_mode="bypassPermissions"`. `Bash` có chạy không?

- A. Có, bypass thắng mọi thứ
- B. Không: luật deny thắng cả `bypassPermissions` và cả khi hook đã cho phép
- C. Tuỳ `can_use_tool`

<details><summary>Đáp án</summary>

**B.** Luật deny đứng ngay sau hook trong luồng quyền và không bị mode nào vượt qua.
</details>

**7.** Bạn không đặt `max_turns` và `max_budget_usd`. Agent chạy tối đa bao nhiêu lượt?

- A. 10 lượt
- B. Không giới hạn
- C. Tới khi hết `max_tokens`

<details><summary>Đáp án</summary>

**B.** Mặc định không có trần. Đặt cả hai cho mọi agent chạy không người canh.
</details>

**8.** Lần chạy đầu của một phiên tốn $0,010. Bạn `resume` phiên đó, `ResultMessage` báo `total_cost_usd=0.014`. Cả hai lần tốn bao nhiêu?

- A. $0,024
- B. $0,014
- C. $0,004

<details><summary>Đáp án</summary>

**B.** Kết quả của phiên resume đã gồm chi phí các lần trước. Và đó vẫn là ước tính phía client, không phải hoá đơn.
</details>

**9.** Không đặt `setting_sources`, agent của bạn làm theo một chỉ dẫn lạ. Nguyên nhân có thể là gì?

- A. Mặc định SDK nạp mọi nguồn settings, gồm `CLAUDE.md` của dự án và của `~/.claude`
- B. System prompt mặc định là của Claude Code
- C. Không thể xảy ra

<details><summary>Đáp án</summary>

**A.** Đặt `setting_sources=[]` để bỏ settings user/project/local và `CLAUDE.md`. Nó không cách ly hoàn toàn: policy của quản trị viên, `~/.claude.json` và auto memory vẫn được nạp. System prompt mặc định là bản tối giản, không phải của Claude Code.
</details>

**10.** `query()` ném `ResultError` với `subtype="error_max_turns"`. Bạn còn đọc được `ResultMessage` không?

- A. Không, lỗi ném trước
- B. Có: SDK trả `ResultMessage` trước rồi mới ném lỗi; bắt lỗi quanh vòng `async for`
- C. Chỉ khi dùng `ClaudeSDKClient`

<details><summary>Đáp án</summary>

**B.** Script 03 và `doc_het()` làm đúng như vậy. `ResultError` cũng có `subtype` và `session_id`, và được ném với mọi result lỗi, kể cả `success` kèm `is_error=True`.
</details>
