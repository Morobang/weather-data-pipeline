import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dags"))

from api.weather_extract import (
    fetch_weather,
    save_to_json,
    extract_all_municipalities,
    MUNICIPALITIES,
)


# ============================================================
# FIXTURES
# Reusable test data
# ============================================================

@pytest.fixture
def sample_municipality():
    """A single municipality dict for testing."""
    return {
        "name":     "City of Tshwane",
        "province": "Gauteng",
        "type":     "Metropolitan",
        "lat":      -25.7479,
        "lon":      28.2293,
    }


@pytest.fixture
def sample_api_response():
    """A fake but realistic Open-Meteo API response."""
    return {
        "latitude":            -25.7479,
        "longitude":           28.2293,
        "elevation":           1339.0,
        "timezone":            "Africa/Johannesburg",
        "timezone_abbreviation": "GMT+2",
        "utc_offset_seconds":  7200,
        "hourly_units": {
            "time":                 "iso8601",
            "temperature_2m":       "°C",
            "precipitation":        "mm",
            "windspeed_10m":        "km/h",
            "relativehumidity_2m":  "%",
            "cloudcover":           "%",
            "visibility":           "m",
            "uv_index":             "",
            "surface_pressure":     "hPa",
        },
        "hourly": {
            "time":                 [f"2026-06-23T{h:02d}:00" for h in range(24)],
            "temperature_2m":       [15.0 + h * 0.5 for h in range(24)],
            "precipitation":        [0.0] * 20 + [0.1, 0.2, 0.1, 0.0],
            "windspeed_10m":        [10.0 + h * 0.2 for h in range(24)],
            "relativehumidity_2m":  [60 + h for h in range(24)],
            "cloudcover":           [20] * 24,
            "visibility":           [40000.0] * 24,
            "uv_index":             [0.0] * 6 + [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0, 1.0, 0.5, 0.0] + [0.0] * 6,
            "surface_pressure":     [1013.0 + h * 0.1 for h in range(24)],
        },
        "daily_units": {
            "time":                 "iso8601",
            "temperature_2m_max":   "°C",
            "temperature_2m_min":   "°C",
            "precipitation_sum":    "mm",
            "windspeed_10m_max":    "km/h",
            "sunrise":              "iso8601",
            "sunset":               "iso8601",
            "daylight_duration":    "s",
            "weathercode":          "wmo code",
        },
        "daily": {
            "time":               ["2026-06-23"],
            "temperature_2m_max": [26.5],
            "temperature_2m_min": [12.0],
            "precipitation_sum":  [0.4],
            "windspeed_10m_max":  [18.0],
            "sunrise":            ["2026-06-23T06:45"],
            "sunset":             ["2026-06-23T17:30"],
            "daylight_duration":  [38700.0],
            "weathercode":        [2],
        },
    }


# ============================================================
# MUNICIPALITIES LIST TESTS
# ============================================================

def test_municipalities_list_not_empty():
    """MUNICIPALITIES list must not be empty."""
    assert len(MUNICIPALITIES) > 0


def test_municipalities_count():
    """Should have exactly 254 municipalities."""
    assert len(MUNICIPALITIES) == 254


def test_each_municipality_has_required_keys():
    """Every municipality must have name, province, type, lat, lon."""
    required_keys = {"name", "province", "type", "lat", "lon"}
    for municipality in MUNICIPALITIES:
        assert required_keys.issubset(municipality.keys()), \
            f"Municipality missing keys: {municipality['name']}"


def test_municipality_types_are_valid():
    """Municipality type must be Metropolitan, District or Local."""
    valid_types = {"Metropolitan", "District", "Local"}
    for municipality in MUNICIPALITIES:
        assert municipality["type"] in valid_types, \
            f"Invalid type for {municipality['name']}: {municipality['type']}"


def test_all_9_provinces_covered():
    """All 9 SA provinces must be in the list."""
    expected_provinces = {
        "Eastern Cape",
        "Free State",
        "Gauteng",
        "KwaZulu-Natal",
        "Limpopo",
        "Mpumalanga",
        "North West",
        "Northern Cape",
        "Western Cape",
    }
    actual_provinces = {m["province"] for m in MUNICIPALITIES}
    assert actual_provinces == expected_provinces


def test_coordinates_are_within_sa_bounds():
    """All coordinates must be within South Africa's geographic bounds."""
    # SA bounding box
    LAT_MIN, LAT_MAX = -35.0, -22.0
    LON_MIN, LON_MAX =  16.0,  33.0

    for municipality in MUNICIPALITIES:
        assert LAT_MIN <= municipality["lat"] <= LAT_MAX, \
            f"Latitude out of SA bounds for {municipality['name']}: {municipality['lat']}"
        assert LON_MIN <= municipality["lon"] <= LON_MAX, \
            f"Longitude out of SA bounds for {municipality['name']}: {municipality['lon']}"


def test_no_duplicate_municipality_names():
    """No two municipalities in the same province should have the same name."""
    seen = set()
    for m in MUNICIPALITIES:
        key = (m["name"], m["province"])
        assert key not in seen, f"Duplicate municipality: {m['name']} in {m['province']}"
        seen.add(key)


# ============================================================
# FETCH WEATHER TESTS
# ============================================================

def test_fetch_weather_returns_correct_structure(sample_municipality, sample_api_response):
    """fetch_weather() must return a dict with the right keys."""
    with patch("api.weather_extract.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = sample_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_weather(sample_municipality)

    assert result is not None
    assert "municipality" in result
    assert "province"     in result
    assert "type"         in result
    assert "lat"          in result
    assert "lon"          in result
    assert "fetched_at"   in result
    assert "data"         in result


def test_fetch_weather_maps_municipality_name(sample_municipality, sample_api_response):
    """fetch_weather() must preserve the municipality name."""
    with patch("api.weather_extract.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = sample_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_weather(sample_municipality)

    assert result["municipality"] == "City of Tshwane"
    assert result["province"]     == "Gauteng"
    assert result["type"]         == "Metropolitan"


def test_fetch_weather_returns_none_on_timeout(sample_municipality):
    """fetch_weather() must return None after all retries fail."""
    import requests as req
    with patch("api.weather_extract.requests.get") as mock_get:
        mock_get.side_effect = req.exceptions.Timeout()

        result = fetch_weather(sample_municipality, retries=1)

    assert result is None


def test_fetch_weather_contains_24_hourly_readings(sample_municipality, sample_api_response):
    """fetch_weather() must return 24 hourly readings."""
    with patch("api.weather_extract.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = sample_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_weather(sample_municipality)

    assert len(result["data"]["hourly"]["time"]) == 24


def test_fetch_weather_contains_daily_data(sample_municipality, sample_api_response):
    """fetch_weather() must return daily summary data."""
    with patch("api.weather_extract.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = sample_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_weather(sample_municipality)

    daily = result["data"]["daily"]
    assert "temperature_2m_max" in daily
    assert "temperature_2m_min" in daily
    assert "precipitation_sum"  in daily
    assert "weathercode"        in daily
    assert "sunrise"            in daily
    assert "sunset"             in daily


# ============================================================
# SAVE TO JSON TESTS
# ============================================================

def test_save_to_json_creates_file(tmp_path, sample_municipality, sample_api_response):
    """save_to_json() must create a JSON file."""
    with patch("api.weather_extract.DATA_DIR", str(tmp_path)):
        records = [{
            "municipality": sample_municipality["name"],
            "province":     sample_municipality["province"],
            "type":         sample_municipality["type"],
            "lat":          sample_municipality["lat"],
            "lon":          sample_municipality["lon"],
            "fetched_at":   "2026-06-23T12:00:00",
            "data":         sample_api_response,
        }]
        filepath = save_to_json(records)

    assert Path(filepath).exists()


def test_save_to_json_content_is_valid(tmp_path, sample_municipality, sample_api_response):
    """save_to_json() must write valid JSON that can be read back."""
    with patch("api.weather_extract.DATA_DIR", str(tmp_path)):
        records = [{
            "municipality": sample_municipality["name"],
            "province":     sample_municipality["province"],
            "type":         sample_municipality["type"],
            "lat":          sample_municipality["lat"],
            "lon":          sample_municipality["lon"],
            "fetched_at":   "2026-06-23T12:00:00",
            "data":         sample_api_response,
        }]
        filepath = save_to_json(records)

    with open(filepath, "r") as f:
        loaded = json.load(f)

    assert len(loaded) == 1
    assert loaded[0]["municipality"] == "City of Tshwane"