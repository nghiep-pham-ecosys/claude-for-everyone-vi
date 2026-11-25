"""Module 06: message threads (beta): each turn sends only the new message, the API keeps the conversation.

A thread makes the request SMALLER and the time to first token steadier. Docs: a thread does NOT change the
price. To pay less, you still need prompt caching: send the same top-level cache_control in every request of
the thread.

A thread is kept only for a short time (it expires 5 minutes after the last request). Your app is still the
source of truth: keep your own copy of the whole conversation, and when a continue gets a 404, resend the
whole conversation with a new create request.

Run:  CLAUDE_MOCK=1 uv run python en/modules/06-cost/python/05_message_threads.py
"""
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "shared" / "py"))

from claude_vi import ClaudeVi, check_request, estimate_cost_usd, text_of  # noqa: E402

SO_TAY = (ROOT / "modules" / "06-cost" / "data" / "so_tay_thiet_bi.md").read_text("utf-8")  # the handbook
CACHE = {"type": "ephemeral"}  # top-level cache_control: fixed for the whole thread


class HoiThoaiThread:
    """A conversation (hoi thoai) on a message thread that resends the whole conversation when the API
    reports thread_not_found.

    It does part of the job of the SDK helper in the docs (the helper also resends on
    thread_already_continued and thread_continue_in_flight).

    Each turn writes to self.nhat_ky (the log): the number of messages SENT and the usage, to show that the
    request gets smaller but the cost does not.
    """

    def __init__(self, client: ClaudeVi, system: str, **co_dinh) -> None:
        self.client = client
        self.system = system
        # model, thinking, output_config, cache_control...: the same (co dinh = fixed) in every request
        self.co_dinh = {"model": client.settings.model, **co_dinh}
        self.messages: list[dict] = []  # the app's own copy: the source of truth
        self.id_truoc: str | None = None  # the id of the previous response
        self.nhat_ky: list[dict] = []

    def _tao(self) -> anthropic.types.Message:
        """The create request: send the system prompt and the WHOLE conversation."""
        return self.client.create(system=self.system, messages=self.messages, thread={"type": "create"},
                                  **self.co_dinh)

    def gui(self, text: str) -> str:
        """Send (gui) one user turn and return the text of the answer."""
        new = {"role": "user", "content": text}
        self.messages.append(new)
        # A continue request holds only the new message: check the rules on the full copy before sending
        check_request({"system": self.system, "messages": self.messages, **self.co_dinh})
        how = "create"
        if self.id_truoc is None:
            msg = self._tao()
        else:
            try:
                msg = self.client.create(messages=[new], **self.co_dinh,
                                         thread={"type": "continue", "previous_message_id": self.id_truoc})
                how = "continue"
            except anthropic.NotFoundError as e:
                # A 404 can also mean the model does not exist: resend only on the exact code thread_not_found
                code = ((e.body or {}).get("error") or {}).get("details", {}).get("error_code")
                if code != "thread_not_found":
                    raise
                msg, how = self._tao(), "resend (404)"  # the API cannot continue: replay everything
        # keep the thinking blocks as they are
        self.messages.append({"role": "assistant", "content": msg.content})
        self.id_truoc = msg.id
        sent = 1 if how == "continue" else len(self.messages) - 1
        self.nhat_ky.append({"cach": how, "so_message_gui": sent, "usage": msg.usage,
                             "usd": estimate_cost_usd(msg)})
        return text_of(msg)


def in_luot(i: int, dong: dict) -> None:
    """Print one turn (in luot) from a log line (dong)."""
    u = dong["usage"]
    print(f"   turn {i} {dong['cach']:<14} sent {dong['so_message_gui']} message(s)"
          f" | input {u.input_tokens:>3}"
          f" write {u.cache_creation_input_tokens or 0:>3} read {u.cache_read_input_tokens or 0:>4}"
          f" | ${dong['usd']:.7f}")


def main() -> None:
    client = ClaudeVi()
    questions = ["What is the maximum temperature of the LN-1200 furnace?",
                 "Which gas does it need, at what flow?",
                 "When may the furnace door be opened?"]

    print("1) A thread WITHOUT cache_control: the request gets smaller, but no token is cached")
    t = HoiThoaiThread(client, SO_TAY)
    for q in questions:
        t.gui(q)
    for i, line in enumerate(t.nhat_ky, 1):
        in_luot(i, line)

    print("\n2) A thread WITH a top-level cache_control: each turn reads the old part from the cache,"
          "\n   writes the new turn")
    t = HoiThoaiThread(client, SO_TAY, cache_control=CACHE)
    for q in questions:
        t.gui(q)
    for i, line in enumerate(t.nhat_ky, 1):
        in_luot(i, line)

    if client.mock is not None:
        print("\n3) Simulate an expired thread (mock only): the continue gets a 404"
              " -> resend the whole conversation")
        client.mock.messages.het_han_threads()  # het han = expire
        t.gui("Sum up the three points above in one sentence.")
        in_luot(len(t.nhat_ky), t.nhat_ky[-1])

    print("\n   The total input (input + write + read) above is always the WHOLE conversation: the mock"
          "\n   assumes the old part is still billed as if it were resent. The docs only say a thread does"
          "\n   not change the price; only numbers measured on a real run count.")


if __name__ == "__main__":
    main()
