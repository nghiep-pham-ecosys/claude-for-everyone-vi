"""Cấu hình pytest chung cho tests/, modules/, capstones/.

Fixture ghi bằng CLAUDE_RECORD=1 nằm ở shared/py/claude_vi/fixtures/ và mock sẽ dùng lại chúng khi
chạy script. Test thì cần kết quả mock cố định ("[MOCK] ..."), nên mỗi test được trỏ tới một thư mục
fixture rỗng. Test nào cần fixture riêng thì tự truyền MockAnthropic(record_dir=...).
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _co_lap_fixture_ghi_that(tmp_path_factory, monkeypatch):
    import claude_vi.mock

    monkeypatch.setattr(claude_vi.mock, "FIXTURE_DIR", tmp_path_factory.mktemp("fixtures_rong"))
