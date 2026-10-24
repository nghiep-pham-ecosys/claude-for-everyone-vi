"""Hai tool mẫu dùng chung cho các script module 03 (dữ liệu bịa, không gọi dịch vụ thật)."""

THANH_PHO = ["Hà Nội", "Đà Nẵng", "TP.HCM"]
_AQI = {"Hà Nội": 152, "Đà Nẵng": 48, "TP.HCM": 97}
_NHIET_DO = {"Hà Nội": 24.5, "Đà Nẵng": 28.0, "TP.HCM": 31.2}

TRA_AQI = {
    "name": "moi_truong_tra_aqi",
    "description": (
        "Tra chỉ số chất lượng không khí (AQI, thang US EPA 0–500) hiện tại của một thành phố Việt Nam. "
        "Dùng khi người dùng hỏi về ô nhiễm không khí, bụi mịn hoặc có nên ra ngoài không. "
        "Chỉ trả về một con số AQI và thời điểm đo; không trả về nồng độ từng chất ô nhiễm. "
        "Chỉ hỗ trợ các thành phố trong danh sách enum."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {"thanh_pho": {"type": "string", "enum": THANH_PHO, "description": "Tên thành phố"}},
        "required": ["thanh_pho"],
        "additionalProperties": False,
    },
}

TRA_NHIET_DO = {
    "name": "moi_truong_tra_nhiet_do",
    "description": (
        "Tra nhiệt độ không khí hiện tại (độ C) của một thành phố Việt Nam. "
        "Dùng khi người dùng hỏi về thời tiết nóng lạnh. Không trả về dự báo. "
        "Chỉ hỗ trợ các thành phố trong danh sách enum."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {"thanh_pho": {"type": "string", "enum": THANH_PHO}},
        "required": ["thanh_pho"],
        "additionalProperties": False,
    },
}


def tra_aqi(thanh_pho: str) -> dict:
    return {"thanh_pho": thanh_pho, "aqi": _AQI[thanh_pho], "do_luc": "2026-10-24T08:00+07:00"}


def tra_nhiet_do(thanh_pho: str) -> dict:
    return {"thanh_pho": thanh_pho, "nhiet_do_c": _NHIET_DO[thanh_pho]}


REGISTRY = {TRA_AQI["name"]: tra_aqi, TRA_NHIET_DO["name"]: tra_nhiet_do}
