"""Two sample tools shared by the module 03 scripts (tools_mau = sample tools).

The data is made up; no real service is called.
"""

CITIES = ["Hanoi", "Da Nang", "Ho Chi Minh City"]
_AQI = {"Hanoi": 152, "Da Nang": 48, "Ho Chi Minh City": 97}
_TEMPERATURE = {"Hanoi": 24.5, "Da Nang": 28.0, "Ho Chi Minh City": 31.2}

GET_AQI = {
    "name": "env_get_aqi",
    "description": (
        "Get the current air quality index (AQI, US EPA scale 0–500) of a city in Vietnam. "
        "Use it when the user asks about air pollution, fine dust, or whether to go outside. "
        "Returns only one AQI number and the time of the reading; it does not return each pollutant. "
        "Only the cities in the enum list are supported."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {"city": {"type": "string", "enum": CITIES, "description": "City name"}},
        "required": ["city"],
        "additionalProperties": False,
    },
}

GET_TEMPERATURE = {
    "name": "env_get_temperature",
    "description": (
        "Get the current air temperature (degrees C) of a city in Vietnam. "
        "Use it when the user asks whether it is hot or cold. It does not return a forecast. "
        "Only the cities in the enum list are supported."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {"city": {"type": "string", "enum": CITIES}},
        "required": ["city"],
        "additionalProperties": False,
    },
}


def get_aqi(city: str) -> dict:
    return {"city": city, "aqi": _AQI[city], "measured_at": "2026-10-24T08:00+07:00"}


def get_temperature(city: str) -> dict:
    return {"city": city, "temperature_c": _TEMPERATURE[city]}


REGISTRY = {GET_AQI["name"]: get_aqi, GET_TEMPERATURE["name"]: get_temperature}
