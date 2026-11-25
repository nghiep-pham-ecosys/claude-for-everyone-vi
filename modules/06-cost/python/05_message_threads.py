"""Module 06 — message threads (beta): mỗi lượt chỉ gửi message mới, API giữ hội thoại trên server.

Thread làm request NHỎ hơn và time to first token ổn định hơn. Docs: thread KHÔNG đổi giá. Muốn rẻ hơn thì vẫn
phải bật prompt caching: gửi cùng một cache_control cấp cao nhất ở mọi request của thread.

Thread chỉ giữ tạm (hết hạn 5 phút sau request cuối). Ứng dụng vẫn là nguồn sự thật: tự giữ bản sao cả hội thoại,
khi continue nhận 404 thì gửi lại cả hội thoại bằng một request create mới.

Chạy:  CLAUDE_MOCK=1 uv run python modules/06-cost/python/05_message_threads.py
"""
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared" / "py"))

from claude_vi import ClaudeVi, check_request, estimate_cost_usd, text_of  # noqa: E402

SO_TAY = (Path(__file__).resolve().parents[1] / "data" / "so_tay_thiet_bi.md").read_text("utf-8")
CACHE = {"type": "ephemeral"}  # cache_control cấp cao nhất: cố định suốt thread


class HoiThoaiThread:
    """Một hội thoại dùng message thread, tự gửi lại cả hội thoại khi API báo thread_not_found.

    Làm một phần việc của SDK helper trong docs (helper còn gửi lại khi gặp thread_already_continued và
    thread_continue_in_flight).

    Mỗi lượt ghi vào self.nhat_ky: số message đã GỬI đi và usage, để thấy request nhỏ lại còn chi phí thì không.
    """

    def __init__(self, client: ClaudeVi, system: str, **co_dinh) -> None:
        self.client = client
        self.system = system
        # model, thinking, output_config, cache_control...: phải giống nhau ở mọi request của thread
        self.co_dinh = {"model": client.settings.model, **co_dinh}
        self.messages: list[dict] = []  # bản sao của ứng dụng: nguồn sự thật
        self.id_truoc: str | None = None
        self.nhat_ky: list[dict] = []

    def _tao(self) -> anthropic.types.Message:
        """Request create: gửi system và CẢ hội thoại."""
        return self.client.create(system=self.system, messages=self.messages, thread={"type": "create"},
                                  **self.co_dinh)

    def gui(self, text: str) -> str:
        moi = {"role": "user", "content": text}
        self.messages.append(moi)
        # Request continue chỉ có message mới: kiểm luật trên bản sao đầy đủ trước khi gửi
        check_request({"system": self.system, "messages": self.messages, **self.co_dinh})
        cach = "create"
        if self.id_truoc is None:
            msg = self._tao()
        else:
            try:
                msg = self.client.create(messages=[moi], **self.co_dinh,
                                         thread={"type": "continue", "previous_message_id": self.id_truoc})
                cach = "continue"
            except anthropic.NotFoundError as e:
                # 404 còn có thể là model không tồn tại: chỉ gửi lại khi đúng mã thread_not_found
                if ((e.body or {}).get("error") or {}).get("details", {}).get("error_code") != "thread_not_found":
                    raise
                msg, cach = self._tao(), "gửi lại (404)"  # API không continue được: replay cả hội thoại
        self.messages.append({"role": "assistant", "content": msg.content})  # giữ nguyên block thinking
        self.id_truoc = msg.id
        self.nhat_ky.append({"cach": cach, "so_message_gui": 1 if cach == "continue" else len(self.messages) - 1,
                             "usage": msg.usage, "usd": estimate_cost_usd(msg)})
        return text_of(msg)


def in_luot(i: int, dong: dict) -> None:
    u = dong["usage"]
    print(f"   lượt {i} {dong['cach']:<14} gửi {dong['so_message_gui']} message | input {u.input_tokens:>3}"
          f" ghi {u.cache_creation_input_tokens or 0:>3} đọc {u.cache_read_input_tokens or 0:>4} | ${dong['usd']:.7f}")


def main() -> None:
    client = ClaudeVi()
    cau_hoi = ["Lò LN-1200 nóng tối đa bao nhiêu?", "Cần khí gì, lưu lượng bao nhiêu?",
               "Khi nào được mở cửa lò?"]

    print("1) Thread KHÔNG có cache_control: request nhỏ lại, nhưng không có token nào được cache")
    t = HoiThoaiThread(client, SO_TAY)
    for c in cau_hoi:
        t.gui(c)
    for i, dong in enumerate(t.nhat_ky, 1):
        in_luot(i, dong)

    print("\n2) Thread CÓ cache_control cấp cao nhất: mỗi lượt đọc phần cũ từ cache, ghi lượt mới")
    t = HoiThoaiThread(client, SO_TAY, cache_control=CACHE)
    for c in cau_hoi:
        t.gui(c)
    for i, dong in enumerate(t.nhat_ky, 1):
        in_luot(i, dong)

    if client.mock is not None:
        print("\n3) Giả lập thread hết hạn (chỉ ở mock): continue nhận 404 -> gửi lại cả hội thoại")
        client.mock.messages.het_han_threads()
        t.gui("Tóm tắt ba ý trên trong một câu.")
        in_luot(len(t.nhat_ky), t.nhat_ky[-1])

    print("\n   Tổng input (input + ghi + đọc) ở trên luôn là CẢ hội thoại: mock giả định phần cũ vẫn bị tính tiền"
          "\n   như khi gửi lại. Docs chỉ nói thread không đổi giá; số đo khi chạy thật mới là căn cứ.")


if __name__ == "__main__":
    main()
