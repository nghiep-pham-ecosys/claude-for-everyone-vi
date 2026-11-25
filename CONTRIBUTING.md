# Đóng góp

Cảm ơn bạn muốn góp sức. Repo này là lộ trình học **không chính thức**, không được Anthropic bảo trợ. Mọi thứ chạy ở **mock mode**: bạn không cần API key và không tốn tiền để đóng góp.

Có câu hỏi hoặc ý tưởng chưa thành issue? Hỏi ở [Discussions](https://github.com/nghiep-pham-ecosys/claude-for-everyone-vi/discussions).

## Bạn có thể giúp gì

- **Sửa lỗi** trong bài đọc, script, bài tập, quiz: chính tả, giải thích sai, link hỏng, dữ kiện đã cũ.
- **Báo lỗi** bằng form "Báo lỗi" ở tab Issues.
- **Module 11–15** (Claude Code, Agent Skills, Evals, Production, Research) mở cho cộng đồng. Bước đầu của mỗi module là một đề cương, có sẵn trong các issue [`good first issue`](https://github.com/nghiep-pham-ecosys/claude-for-everyone-vi/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

Việc lớn (module mới, đổi wrapper `claude_vi`, đổi cấu trúc repo): mở issue hoặc thảo luận trước khi viết code. Đề cương được duyệt rồi mới viết module, giống [đề cương module 08](docs/de-cuong-module-08.md).

## Quy trình

1. **Nhận việc.** Comment vào issue rằng bạn nhận làm, để hai người không làm trùng.
2. **Fork hoặc nhánh.** Người ngoài fork repo rồi làm trên fork. Người có quyền ghi tạo nhánh ngay trong repo. Tên nhánh: `<type>/<số issue>-<mô-tả-ngắn>`, ví dụ `docs/12-de-cuong-module-11`.
3. **Bật hook pre-push** một lần sau khi clone: `git config core.hooksPath .githooks`. Hook chạy gitleaks và chặn push có secret.
4. **Commit** theo [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`. Mỗi commit một việc.
5. **Chạy 4 lệnh** ở mục dưới. Cả 4 phải xanh.
6. **Mở PR vào `main`.** Điền template PR. Thân PR ghi `Refs #<số issue>`. Không dùng `Fixes`, `Closes` hay `Resolves`: issue chỉ đóng sau khi chủ dự án kiểm lại trên `main`.

### Tên PR

PR được merge kiểu squash, nên **tên PR trở thành commit trên `main`**. Check `pr-title` kiểm tên PR theo mẫu:

```text
^(feat|fix|chore|refactor|docs|test|ci)(\([a-z0-9-]+\))?!?: .+
```

Ví dụ: `docs: outline module 11 on claude code`, `fix(module-04): broken link in references`. Tên sai thì sửa tên PR, không cần commit lại.

## 4 lệnh chạy trên máy

```bash
uv sync
CLAUDE_MOCK=1 uv run pytest -q                                           # wrapper, luật model, bài tập (mock)
uv run python scripts/check_models.py                                    # model ID phải nằm trong config/models.yaml
uv run python scripts/check_legacy_params.py                             # chặn pattern đã hỏng trên model 5.x
CLAUDE_MOCK=1 uv run python modules/01-messages-api/python/01_hello.py   # script mẫu chạy ở mock mode
```

CI (`ci.yml`) chạy cùng các lệnh này, cộng thêm mọi script `modules/*/python/*.py`, capstone và gitleaks. Đổi README module thì dựng thử trang: `uv run python scripts/build_site.py --out _site`.

## Chỉ dùng mock mode

- **Không dùng API key thật.** Đặt `CLAUDE_MOCK=1`. Mock trả response đã validate bằng kiểu dữ liệu của SDK, nên test vẫn bắt được lỗi hình dạng request.
- **Không commit `.env`** hay bất kỳ key, token nào. Hook pre-push và job `gitleaks` chặn, nhưng đừng dựa vào chúng.
- **Không ghi fixture từ API thật** (`CLAUDE_RECORD=1`). Chủ dự án ghi fixture khi có key. Test cần dữ liệu thì tự viết trong test.
- Job `live-smoke` và `model-sync` gọi API thật. Chỉ chủ dự án chạy, và chúng đang tắt hoặc chỉ chạy tay.
- Mock thiếu tính năng bài của bạn cần? Mở issue mô tả request và response mong muốn, kèm link docs chính thức. Đừng gọi `Anthropic()` trực tiếp để vượt qua.

## Review và merge

- **Ai review:** chủ dự án, GitHub [`pqnghiep1354`](https://github.com/pqnghiep1354). Lần đầu bạn mở PR từ fork, workflow CI chờ chủ dự án bấm duyệt rồi mới chạy (thiết lập mặc định của GitHub cho người đóng góp lần đầu).
- **Điều kiện merge:** check `ci-result` và `pr-title` xanh, không xung đột với `main`, các góp ý review đã xử lý.
- **Ai merge:** chủ dự án, kiểu squash. Nhánh tự xoá sau khi merge.
- PR chỉ làm một việc. PR lớn hoặc trộn nhiều việc sẽ được đề nghị tách.

## Giấy phép của phần đóng góp

Khi mở PR, bạn đồng ý cấp phép phần đóng góp theo đúng giấy phép của repo:

- **Code** (script, test, wrapper, checker, workflow): [MIT](LICENSE).
- **Nội dung bài giảng** (văn bản, hình minh hoạ, quiz, dữ liệu mẫu tự viết): [CC BY 4.0](LICENSE-CONTENT).

Chỉ gửi phần bạn tự viết, hoặc phần có giấy phép tương thích kèm ghi nguồn trong [NOTICE.md](NOTICE.md). Không chép nội dung CC BY-NC hoặc không có giấy phép (xem NOTICE.md).

## Quy tắc viết

- **Gọi Claude qua `claude_vi.ClaudeVi`**, không tạo `Anthropic()` trực tiếp trong bài học.
- **Không viết `msg.content[0].text`.** Dùng `text_of(msg)` — trên model 5.x block đầu có thể là `thinking`.
- **Không dùng** `temperature`, `top_p`, `top_k`, `budget_tokens`, prefill assistant, `tool_choice` any/tool. Muốn minh hoạ cách cũ → đặt trong `legacy/` và ghi rõ "chỉ để đọc".
- **Model mới:** thêm vào `config/models.yaml` kèm link release note. Không viết model ID ở nơi khác.
- **Notebook:** xoá output trước khi commit (`nbstripout`).
- **Mỗi module có `references.md`** ghi link chính thức và ngày kiểm tra. Dữ kiện về sản phẩm, giá, model phải kiểm từ [docs chính thức](https://platform.claude.com/docs) hiện tại.
- **Capstone và ví dụ khoa học:** không đề bài liên quan tổng hợp chất nguy hiểm, mầm bệnh, vũ khí.
- **Văn phong:** tiếng Việt, câu ngắn, giải thích "vì sao" trước "làm thế nào". Giữ tên kỹ thuật tiếng Anh, lần đầu xuất hiện thì giải thích.

### Thêm một module mới

Theo khuôn [module 01](modules/01-messages-api/README.md):

- Thư mục `modules/NN-ten/` có `README.md`, `python/`, `exercises/`, `solutions/`, `tests/test_moduleNN.py`, `quiz.md`, `references.md`.
- Thêm một mục cho module vào [`docs/pages/videos.yaml`](docs/pages/videos.yaml), để `video: ""`. Thiếu mục này thì build trang báo lỗi.
- Thêm một dòng vào bảng "Lộ trình" trong [README.md](README.md).

## Bảo mật

Thấy secret bị lộ hoặc lỗ hổng bảo mật: **đừng mở issue công khai**. Báo riêng qua tab **Security** → **Report a vulnerability** của repo.
