"""Kiểm script ước tính chi phí của module 06 (mock mode, không gọi mạng, không cần key).

    uv run pytest modules/06-cost -q
"""
import importlib.util
import math
import sys
from pathlib import Path

import anthropic
import pytest
from claude_vi import estimate_cost_usd, load_models
from claude_vi.cham import tao_client

MODULE = Path(__file__).resolve().parents[1]
MODELS = load_models()["models"]
ACTIVE = [m for m, e in MODELS.items() if e.get("status") == "active"]
KHONG_GIA = [m for m, e in MODELS.items() if not e.get("price_per_mtok")]


def _nap_script():
    path = MODULE / "python" / "01_uoc_tinh_chi_phi.py"
    spec = importlib.util.spec_from_file_location("module06_uoc_tinh_chi_phi", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # chỉ định nghĩa hàm; main() chạy khi gọi trực tiếp
    return mod


S = _nap_script()


@pytest.mark.parametrize("model", ACTIVE)
def test_tran_output_doc_gia_tu_config(model):
    gia = MODELS[model]["price_per_mtok"]
    assert S.gia(model) == gia
    assert S.tran_chi_phi_output(model, 1024) == pytest.approx(1024 * gia["output"] / 1e6)


@pytest.mark.parametrize("model", KHONG_GIA)
def test_model_chua_co_gia_tra_nan(model):
    assert S.gia(model) is None
    assert math.isnan(S.tran_chi_phi_output(model, 1024))


@pytest.mark.parametrize("model", ACTIVE)
@pytest.mark.parametrize("effort", ["low", "high"])
def test_tach_chi_phi_khop_estimate_va_duoi_tran(model, effort):
    client, mock = tao_client()
    max_tokens = 256
    msg = client.ask("x", model=model, max_tokens=max_tokens, output_config={"effort": effort})
    assert mock.messages.calls == 1  # đi qua mock, không qua mạng

    c, gia, u = S.tach_chi_phi(msg), MODELS[model]["price_per_mtok"], msg.usage
    assert c["input"] == pytest.approx(u.input_tokens * gia["input"] / 1e6)
    assert c["output"] == pytest.approx(u.output_tokens * gia["output"] / 1e6)
    assert c["tong"] == pytest.approx(estimate_cost_usd(msg))
    assert 0 < c["thinking"] <= c["output"]  # thinking nằm trong output, không cộng thêm
    assert c["output"] <= S.tran_chi_phi_output(model, max_tokens)
    assert c["token_cache_chua_tinh"] == 0


def test_main_chay_mock_khong_can_key(monkeypatch, capsys):
    monkeypatch.setenv("CLAUDE_MOCK", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    def cam_goi_that(*a, **k):
        raise AssertionError("script không được tạo client thật")

    monkeypatch.setattr(anthropic, "Anthropic", cam_goi_that)
    S.main()
    out = capsys.readouterr().out
    assert "estimate_cost_usd" in out
    for model in ACTIVE:
        assert model in out
