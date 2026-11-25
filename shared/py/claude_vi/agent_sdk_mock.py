"""Mock của Claude Agent SDK (gói `claude-agent-sdk`) cho module 09: cùng tên, cùng hình dạng, không gọi mạng.

Tên lớp, tên trường và luồng message chép theo docs và mã nguồn claude-agent-sdk 0.2.189 (kiểm 2026-11-25,
xem modules/09-agent-sdk/references.md). Chỉ có phần bài học dùng tới. Mock KHÔNG chạy Claude Code CLI, không có
tool dựng sẵn (Read, Bash...): chỉ chạy tool tự viết bằng @tool + create_sdk_mcp_server.

Cách mock "suy nghĩ": mỗi lượt gọi MỘT tool tự viết chưa gọi (theo thứ tự trong mcp_servers), input tối thiểu theo
schema; gọi hết thì trả lời bằng text. Giống MockAnthropic(multi_step=True) của module 08.

Luồng quyền (docs Permissions, rút gọn): hook PreToolUse -> disallowed_tools -> permission_mode -> allowed_tools
-> can_use_tool -> không ai duyệt thì từ chối. Mock không có bước "ask rules" và không xử lý interrupt.
"""
from __future__ import annotations

import asyncio
import dataclasses
import fnmatch
import json
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from .config import load_models
from .mock import _KY_TU_MOI_TOKEN, _TEXT_TOKENS, _THINKING_BY_EFFORT, schema_instance

__version__ = "0.0.0-mock"

PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"]


# ---------- Content blocks và message ----------

@dataclass
class TextBlock:
    text: str


@dataclass
class ThinkingBlock:
    thinking: str
    signature: str


@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None


@dataclass
class UserMessage:
    content: str | list[Any]
    uuid: str | None = None
    parent_tool_use_id: str | None = None
    tool_use_result: dict[str, Any] | None = None


@dataclass
class AssistantMessage:
    content: list[Any]
    model: str
    parent_tool_use_id: str | None = None
    error: str | None = None
    usage: dict[str, Any] | None = None
    message_id: str | None = None
    stop_reason: str | None = None
    session_id: str | None = None
    uuid: str | None = None


@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]


@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    stop_reason: str | None = None
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
    structured_output: Any = None
    model_usage: dict[str, Any] | None = None
    permission_denials: list[Any] | None = None
    errors: list[str] | None = None
    terminal_reason: str | None = None


# ---------- Quyền và hook ----------

@dataclass
class ToolPermissionContext:
    signal: Any | None = None
    suggestions: list[Any] = field(default_factory=list)
    tool_use_id: str | None = None
    agent_id: str | None = None


@dataclass
class PermissionResultAllow:
    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None
    updated_permissions: list[Any] | None = None


@dataclass
class PermissionResultDeny:
    behavior: Literal["deny"] = "deny"
    message: str = ""
    interrupt: bool = False


@dataclass
class HookMatcher:
    matcher: str | None = None
    hooks: list[Callable[..., Awaitable[dict[str, Any]]]] = field(default_factory=list)
    timeout: float | None = None
    on_failure: Literal["continue", "block"] | None = None


@dataclass
class AgentDefinition:
    description: str
    prompt: str
    tools: list[str] | None = None
    model: str | None = None


# ---------- Tool tự viết ----------

@dataclass
class SdkMcpTool:
    name: str
    description: str
    input_schema: type | dict[str, Any]
    handler: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]
    annotations: Any = None


def tool(name: str, description: str, input_schema: type | dict[str, Any], annotations: Any = None):
    """@tool(name, description, input_schema): bọc một hàm async nhận MỘT dict tham số."""
    def wrap(handler):
        return SdkMcpTool(name, description, input_schema, handler, annotations)
    return wrap


def create_sdk_mcp_server(name: str, version: str = "1.0.0", tools: list[SdkMcpTool] | None = None) -> dict:
    """Server MCP chạy trong process. Mock giữ danh sách tool trong khoá "instance"."""
    return {"type": "sdk", "name": name, "instance": {"version": version, "tools": list(tools or [])}}


_KIEU = {str: "string", int: "integer", float: "number", bool: "boolean"}


def json_schema(input_schema: Any) -> dict[str, Any]:
    """Dạng đơn giản {"ten": str} -> JSON Schema (mọi khoá bắt buộc, như docs); JSON Schema thì giữ nguyên."""
    if isinstance(input_schema, dict) and input_schema.get("type") == "object":
        return input_schema
    if isinstance(input_schema, dict):
        return {"type": "object", "properties": {k: {"type": _KIEU.get(v, "string")} for k, v in input_schema.items()},
                "required": list(input_schema)}
    raise TypeError("Mock chỉ hỗ trợ input_schema dạng dict (đơn giản hoặc JSON Schema)")


# ---------- Options ----------

@dataclass
class ClaudeAgentOptions:
    tools: list[str] | dict[str, Any] | None = None
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | dict[str, Any] | None = None
    mcp_servers: dict[str, Any] | str = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    max_budget_usd: float | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    cwd: str | None = None
    can_use_tool: Callable[..., Awaitable[Any]] | None = None
    hooks: dict[str, list[HookMatcher]] | None = None
    fork_session: bool = False
    agents: dict[str, AgentDefinition] | None = None
    setting_sources: list[str] | None = None
    effort: str | None = None
    thinking: dict[str, Any] | None = None
    output_format: dict[str, Any] | None = None


# ---------- Lỗi ----------

class ClaudeSDKError(Exception):
    pass


class ProcessError(ClaudeSDKError):
    def __init__(self, message: str, exit_code: int | None = None, stderr: str | None = None) -> None:
        super().__init__(message)
        self.exit_code, self.stderr = exit_code, stderr


class ResultError(ProcessError):
    """Như SDK: query() đơn lẻ kết thúc bằng result lỗi thì trả ResultMessage rồi ném lỗi này."""

    def __init__(self, msg: ResultMessage) -> None:
        super().__init__(f"Lần chạy kết thúc với {msg.subtype}", exit_code=1)
        self.subtype, self.errors, self.result = msg.subtype, list(msg.errors or []), msg.result
        self.session_id, self.terminal_reason, self.api_error_status = msg.session_id, msg.terminal_reason, None
        self.data = {"type": "result", **dataclasses.asdict(msg)}


# ---------- Vòng lặp agent giả lập ----------

_PHIEN: dict[str, dict[str, Any]] = {}   # session_id -> {"chu": độ dài hội thoại, "usd": tổng chi phí}
_DEM = {"phien": 0, "tool": 0, "thu_tu": 0}


def _model(options: ClaudeAgentOptions) -> str:
    """Tên đầy đủ trong config/models.yaml, hoặc alias ("haiku", "sonnet"...) -> model active đầu tiên khớp."""
    cfg = load_models()
    ten = options.model or cfg["default_model"]
    if ten in cfg["models"]:
        return ten
    for m, e in cfg["models"].items():
        if e.get("status") == "active" and f"-{ten}-" in m:
            return m
    raise ValueError(f"Mock không biết model '{ten}'")


_TIEN_TO_SERVER = re.compile(r"^mcp__[^*?\[\]_]+(?:_[^*?\[\]_]+)*__")


def _khop_allow(ten: str, quy_tac: list[str]) -> bool:
    """Luật allow (docs Permissions): trùng tên, hoặc glob SAU tiền tố mcp__<server>__ viết rõ. '*' và 'mcp__*'
    trong allowed_tools bị bỏ qua."""
    for q in quy_tac:
        if q == ten:
            return True
        m = _TIEN_TO_SERVER.match(q)
        if m and ten.startswith(m.group()) and fnmatch.fnmatchcase(ten, q):
            return True
    return False


def _khop_deny(ten: str, quy_tac: list[str]) -> bool:
    """Luật deny nhận cả glob tên tool: '*' (mọi tool), 'mcp__*' (mọi tool MCP), 'mcp__<server>__*'..."""
    return any(q == ten or fnmatch.fnmatchcase(ten, q) for q in quy_tac)


def _matcher_khop(matcher: str | None, ten: str) -> bool:
    """docs Hooks: matcher chỉ gồm chữ, số, '_' và '|' là tên chính xác (hoặc danh sách tên); còn lại là regex."""
    if not matcher:
        return True
    if re.fullmatch(r"[A-Za-z0-9_|]+", matcher):
        return ten in matcher.split("|")
    return re.search(matcher, ten) is not None


@dataclass
class HookContext:
    signal: Any | None = None


async def _chay_hook(options: ClaudeAgentOptions, su_kien: str, du_lieu: dict[str, Any], tool_use_id: str) -> list:
    """Chạy các callback khớp. Callback ném lỗi: mặc định bỏ qua (mở cửa); on_failure="block" thì coi là từ chối,
    kể cả khi callback trả None (docs Hooks)."""
    out = []
    for m in (options.hooks or {}).get(su_kien, []):
        if not _matcher_khop(m.matcher, du_lieu.get("tool_name", "")):
            continue
        for cb in m.hooks:
            try:
                kq = await cb(du_lieu, tool_use_id, HookContext())
                hong = kq is None and m.on_failure == "block"
            except Exception:  # noqa: BLE001  giống SDK: lỗi trong hook không làm sập lần chạy
                kq, hong = {}, m.on_failure == "block"
            if hong:
                kq = {"hookSpecificOutput": {"hookEventName": su_kien, "permissionDecision": "deny",
                                             "permissionDecisionReason": "Hook lỗi, on_failure='block'"}}
            out.append(kq or {})
    return out


def _loi_schema(schema: dict[str, Any], vao: dict[str, Any]) -> str | None:
    """Kiểm tối thiểu như SDK làm trước khi gọi handler: thiếu trường bắt buộc, sai kiểu, ngoài enum."""
    kieu = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "object": dict, "array": list}
    for k in schema.get("required") or []:
        if k not in vao:
            return f"'{k}' is a required property"
    for k, p in (schema.get("properties") or {}).items():
        if k not in vao:
            continue
        t = kieu.get(p.get("type"))
        if t and (not isinstance(vao[k], t) or (p.get("type") in ("integer", "number") and isinstance(vao[k], bool))):
            return f"{vao[k]!r} is not of type '{p['type']}'"
        if "enum" in p and vao[k] not in p["enum"]:
            return f"{vao[k]!r} is not one of {p['enum']}"
    return None


async def _duyet(options: ClaudeAgentOptions, ten: str, vao: dict, tool_use_id: str, phien: str):
    """Trả (cho_phép, input_dùng, lời_nhắn). Thứ tự theo docs Permissions, bỏ bước ask rules."""
    hook = {"session_id": phien, "transcript_path": f"/mock/{phien}.jsonl", "cwd": options.cwd,
            "permission_mode": options.permission_mode or "default", "hook_event_name": "PreToolUse",
            "tool_name": ten, "tool_input": vao, "tool_use_id": tool_use_id}
    quyet = [(o.get("hookSpecificOutput") or {}) for o in await _chay_hook(options, "PreToolUse", hook, tool_use_id)]
    if any(q.get("permissionDecision") == "deny" for q in quyet):
        ly_do = next(q.get("permissionDecisionReason", "") for q in quyet if q.get("permissionDecision") == "deny")
        return False, vao, ly_do or "Hook PreToolUse từ chối"
    if _khop_deny(ten, options.disallowed_tools):
        return False, vao, f"{ten} bị chặn bởi disallowed_tools"
    if any(q.get("permissionDecision") == "allow" for q in quyet):
        return True, vao, ""
    if options.permission_mode == "bypassPermissions":
        return True, vao, ""
    if _khop_allow(ten, options.allowed_tools):
        return True, vao, ""
    if options.permission_mode == "dontAsk" or options.can_use_tool is None:
        return False, vao, f"Chưa được duyệt: {ten} không có trong allowed_tools"
    kq = await options.can_use_tool(ten, vao, ToolPermissionContext(tool_use_id=tool_use_id))
    if isinstance(kq, PermissionResultAllow):
        return True, kq.updated_input or vao, ""
    return False, vao, kq.message or "can_use_tool từ chối"


def _tool_cua(options: ClaudeAgentOptions) -> list[tuple[str, SdkMcpTool]]:
    out = []
    if isinstance(options.mcp_servers, dict):
        for key, cfg in options.mcp_servers.items():
            if isinstance(cfg, dict) and cfg.get("type") == "sdk":
                ten_server = re.sub(r"[.\s]", "_", key)  # docs: '.' và khoảng trắng trong khoá thành '_'
                out += [(f"mcp__{ten_server}__{t.name}", t) for t in cfg["instance"]["tools"]]
    # Tên trần hoặc glob trong disallowed_tools bỏ hẳn tool khỏi danh sách
    return [(ten, t) for ten, t in out if not _khop_deny(ten, options.disallowed_tools)]


def _input_gia(schema: dict[str, Any], prompt: str) -> dict[str, Any]:
    """Input tối thiểu theo schema; chuỗi tự do (không enum, không format) lấy chính prompt, như khi Claude chép
    yêu cầu của người dùng vào tham số. Đủ để hook và can_use_tool có nội dung thật để soi."""
    vao = schema_instance(schema, hint=prompt)
    for k, p in (schema.get("properties") or {}).items():
        if p.get("type") == "string" and "enum" not in p and "format" not in p and k in vao:
            vao[k] = prompt[:200]
    return vao


def _chi_phi(model: str, vao: int, ra: int) -> float:
    gia = load_models()["models"][model]["price_per_mtok"]
    return (vao * gia["input"] + ra * gia["output"]) / 1_000_000


async def query(*, prompt: str, options: ClaudeAgentOptions | None = None, transport: Any = None
                ) -> AsyncIterator[Any]:
    """Như claude_agent_sdk.query(): async iterator các message của MỘT lần chạy agent."""
    options = options or ClaudeAgentOptions()
    if not isinstance(prompt, str):
        raise TypeError("Mock chỉ nhận prompt dạng str")
    model = _model(options)
    if options.continue_conversation and options.resume:
        # Chỉ mock: docs ghi hai tuỳ chọn loại trừ nhau, chưa kiểm SDK thật báo lỗi thế nào
        raise ValueError("continue_conversation và resume không dùng chung được")
    if options.resume and options.resume not in _PHIEN:
        # SDK thật: CLI không tìm thấy hội thoại có id này. Mock: kết thúc bằng result lỗi rồi ném ResultError.
        msg = ResultMessage(subtype="error_during_execution", duration_ms=0, duration_api_ms=0, is_error=True,
                            num_turns=0, session_id=options.resume,
                            errors=[f"No conversation found with session ID: {options.resume}"])
        yield msg
        raise ResultError(msg)
    cu = options.resume or (max(_PHIEN, key=lambda k: _PHIEN[k]["thu_tu"]) if options.continue_conversation and _PHIEN
                            else None)
    if cu and cu in _PHIEN and not options.fork_session:
        phien = cu
    else:
        _DEM["phien"] += 1
        phien = f"00000000-0000-4000-8000-{_DEM['phien']:012d}"
        # fork: phiên mới mang theo hội thoại và tổng chi phí đã lưu của phiên gốc (docs Cost tracking)
        _PHIEN[phien] = {"chu": _PHIEN[cu]["chu"] if cu in _PHIEN else 0,
                         "usd": _PHIEN[cu]["usd"] if cu in _PHIEN else 0.0, "thu_tu": 0}
    trang_thai = _PHIEN[phien]
    _DEM["thu_tu"] += 1
    trang_thai["thu_tu"] = _DEM["thu_tu"]
    tools = _tool_cua(options)

    yield SystemMessage("init", {"session_id": phien, "model": model, "cwd": options.cwd,
                                 "tools": [ten for ten, _ in tools],
                                 "mcp_servers": [{"name": k, "status": "connected"}
                                                 for k in (options.mcp_servers or {})],
                                 "permissionMode": options.permission_mode or "default"})

    system = options.system_prompt if isinstance(options.system_prompt, str) else ""
    trang_thai["chu"] += len(system) + len(prompt) + sum(len(json.dumps(json_schema(t.input_schema))) for _, t in tools)
    effort = options.effort or load_models()["models"][model].get("default_effort", "high")
    thinking = _THINKING_BY_EFFORT.get(effort, 6)
    usd_lan_nay, vao_tong, ra_tong, luot, ket_qua, tu_choi = 0.0, 0, 0, 0, [], []
    stop_cuoi = None  # stop_reason của AssistantMessage gần nhất: result lỗi mang giá trị này

    async def ket_thuc(subtype: str, text: str | None):
        trang_thai["usd"] += usd_lan_nay
        msg = ResultMessage(
            subtype=subtype, duration_ms=0, duration_api_ms=0, is_error=subtype != "success", num_turns=luot,
            session_id=phien, stop_reason="end_turn" if subtype == "success" else stop_cuoi,
            total_cost_usd=trang_thai["usd"],  # docs: phiên resume đã gồm chi phí cũ
            usage={"input_tokens": vao_tong, "output_tokens": ra_tong}, result=text if subtype == "success" else None,
            structured_output=(schema_instance(options.output_format["schema"], hint=prompt)
                               if options.output_format and subtype == "success" else None),
            permission_denials=tu_choi, errors=[] if subtype == "success" else [{
                "error_max_turns": f"Reached maximum number of turns ({options.max_turns})",
                "error_max_budget_usd": f"Reached maximum budget (${options.max_budget_usd})"}.get(subtype, subtype)],
            terminal_reason={"success": "completed", "error_max_turns": "max_turns"}.get(subtype))
        # Mock: luôn gửi đủ usage/total_cost_usd; SDK thật để Optional, code phải kiểm None
        return msg

    for i in range(len(tools) + 1):
        if options.max_turns is not None and luot >= options.max_turns:
            msg = await ket_thuc("error_max_turns", None)
            yield msg
            raise ResultError(msg)
        luot += 1
        vao, ra = -(-trang_thai["chu"] // _KY_TU_MOI_TOKEN), _TEXT_TOKENS + thinking
        vao_tong, ra_tong = vao_tong + vao, ra_tong + ra
        usd_lan_nay += _chi_phi(model, vao, ra)
        if i == len(tools):
            text = "[MOCK] Xong. " + " | ".join(ket_qua) if ket_qua else "[MOCK] Xin chào! Đây là phản hồi giả lập."
            yield AssistantMessage([TextBlock(text)], model, message_id=f"msg_mock_{luot}", session_id=phien,
                                   stop_reason="end_turn")
            yield await ket_thuc("success", text)
            return
        ten, t = tools[i]
        _DEM["tool"] += 1
        tool_use_id = f"toolu_mock_{_DEM['tool']:03d}"
        vao_tool = _input_gia(json_schema(t.input_schema), prompt)
        yield AssistantMessage([ToolUseBlock(tool_use_id, ten, vao_tool)], model, message_id=f"msg_mock_{luot}",
                               session_id=phien, stop_reason="tool_use")
        stop_cuoi = "tool_use"
        duoc, vao_tool, ly_do = await _duyet(options, ten, vao_tool, tool_use_id, phien)
        loi_schema = _loi_schema(json_schema(t.input_schema), vao_tool) if duoc else None
        if loi_schema:  # SDK kiểm input theo schema TRƯỚC handler; sai thì handler không chạy
            noi_dung, loi = [{"type": "text", "text": f"Input validation error: {loi_schema}"}], True
        elif duoc:
            try:
                out = await t.handler(vao_tool)
                noi_dung, loi = out.get("content", []), bool(out.get("is_error"))
            except Exception as e:  # noqa: BLE001  docs: exception trong handler thành kết quả lỗi cho Claude
                noi_dung, loi = [{"type": "text", "text": f"Lỗi: {e}"}], True
            await _chay_hook(options, "PostToolUse", {
                "session_id": phien, "transcript_path": f"/mock/{phien}.jsonl", "cwd": options.cwd,
                "permission_mode": options.permission_mode or "default", "hook_event_name": "PostToolUse",
                "tool_name": ten, "tool_input": vao_tool, "tool_response": noi_dung, "tool_use_id": tool_use_id},
                tool_use_id)
        else:
            noi_dung, loi = [{"type": "text", "text": ly_do}], True
            tu_choi.append({"tool_name": ten, "tool_use_id": tool_use_id, "tool_input": vao_tool})
        chu = " ".join(c.get("text", "") for c in noi_dung if isinstance(c, dict))
        ket_qua.append(("LỖI " if loi else "") + chu[:60])
        trang_thai["chu"] += len(json.dumps(vao_tool, ensure_ascii=False)) + len(chu)
        yield UserMessage([ToolResultBlock(tool_use_id, noi_dung, loi)], parent_tool_use_id=None)
        # docs: kiểm sau mỗi response nên có thể vượt trần một chút; chỉ tính chi phí của lần chạy này
        if options.max_budget_usd is not None and usd_lan_nay >= options.max_budget_usd:
            msg = await ket_thuc("error_max_budget_usd", None)
            yield msg
            raise ResultError(msg)


def _xoa_phien() -> None:
    """Chỉ dùng trong test: quên mọi phiên đã lưu."""
    _PHIEN.clear()
    _DEM.update(phien=0, tool=0, thu_tu=0)


def chay(coro: Awaitable[Any]) -> Any:
    """asyncio.run cho script bài học."""
    return asyncio.run(coro)
