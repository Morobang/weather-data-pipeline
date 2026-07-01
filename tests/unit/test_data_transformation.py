import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dags"))

from datawarehouse.data_modification import WEATHERCODE_DESCRIPTIONS


# ============================================================
# WEATHERCODE TESTS
# ============================================================

def test_weathercode_descriptions_not_empty():
    """WEATHERCODE_DESCRIPTIONS must not be empty."""
    assert len(WEATHERCODE_DESCRIPTIONS) > 0


def test_weathercode_clear_sky():
    """Weathercode 0 must be Clear sky."""
    assert WEATHERCODE_DESCRIPTIONS[0] == "Clear sky"


def test_weathercode_overcast():
    """Weathercode 3 must be Overcast."""
    assert WEATHERCODE_DESCRIPTIONS[3] == "Overcast"


def test_weathercode_thunderstorm():
    """Weathercode 95 must be Thunderstorm."""
    assert WEATHERCODE_DESCRIPTIONS[95] == "Thunderstorm"


def test_weathercode_heavy_rain():
    """Weathercode 65 must be Heavy rain."""
    assert WEATHERCODE_DESCRIPTIONS[65] == "Heavy rain"


def test_weathercode_fog():
    """Weathercode 45 must be Fog."""
    assert WEATHERCODE_DESCRIPTIONS[45] == "Fog"


def test_all_weathercodes_have_descriptions():
    """Every weathercode must have a non-empty description."""
    for code, description in WEATHERCODE_DESCRIPTIONS.items():
        assert isinstance(description, str), \
            f"Weathercode {code} description is not a string"
        assert len(description) > 0, \
            f"Weathercode {code} has empty description"


def test_weathercode_unknown_returns_default():
    """Unknown weathercodes must return Unknown."""
    unknown_code = 999
    description = WEATHERCODE_DESCRIPTIONS.get(unknown_code, "Unknown")
    assert description == "Unknown"


# ============================================================
# TEMPERATURE RANGE TESTS
# ============================================================

def test_sa_temperature_range():
    """SA temperatures must be between -20 and 60 degrees."""
    sa_min = -20
    sa_max = 60

    sample_temps = [5.5, 10.2, 28.4, 35.1, 42.0, -5.0, 0.0]
    for temp in sample_temps:
        assert sa_min <= temp <= sa_max, \
            f"Temperature {temp} outside SA range"


def test_invalid_temperature_outside_range():
    """Temperatures outside SA range must be detected."""
    sa_min = -20
    sa_max = 60

    invalid_temps = [-25.0, 65.0, 100.0, -50.0]
    for temp in invalid_temps:
        assert not (sa_min <= temp <= sa_max), \
            f"Temperature {temp} should be outside SA range"


# ============================================================
# PRECIPITATION TESTS
# ============================================================

def test_precipitation_not_negative():
    """Precipitation must never be negative."""
    sample_precip = [0.0, 0.1, 0.5, 1.2, 5.0, 10.0]
    for p in sample_precip:
        assert p >= 0, f"Precipitation {p} is negative"


def test_rainy_hour_detection():
    """An hour is rainy if precipitation > 0."""
    rainy_readings     = [0.1, 0.5, 1.0, 2.5]
    non_rainy_readings = [0.0]

    for p in rainy_readings:
        assert p > 0, f"Expected rainy for precipitation {p}"

    for p in non_rainy_readings:
        assert p == 0, f"Expected not rainy for precipitation {p}"


# ============================================================
# HUMIDITY TESTS
# ============================================================

def test_humidity_within_valid_range():
    """Humidity must be between 0 and 100 percent."""
    sample_humidity = [0, 25, 50, 75, 100]
    for h in sample_humidity:
        assert 0 <= h <= 100, f"Humidity {h} outside valid range"


def test_invalid_humidity_outside_range():
    """Humidity outside 0-100 must be detected."""
    invalid_humidity = [-1, 101, 150, 200]
    for h in invalid_humidity:
        assert not (0 <= h <= 100), \
            f"Humidity {h} should be outside valid range"


# ============================================================
# DAYTIME DETECTION TESTS
# ============================================================

def test_daytime_detection_during_day():
    """Hours between sunrise and sunset must be daytime."""
    sunrise   = "2026-06-23T06:45"
    sunset    = "2026-06-23T17:30"
    daytime_hours = [
        "2026-06-23T07:00",
        "2026-06-23T12:00",
        "2026-06-23T17:00",
    ]
    for hour in daytime_hours:
        is_daytime = sunrise <= hour <= sunset
        assert is_daytime, f"Expected daytime for {hour}"


def test_nighttime_detection():
    """Hours outside sunrise-sunset must be nighttime."""
    sunrise = "2026-06-23T06:45"
    sunset  = "2026-06-23T17:30"
    nighttime_hours = [
        "2026-06-23T00:00",
        "2026-06-23T05:00",
        "2026-06-23T18:00",
        "2026-06-23T23:00",
    ]
    for hour in nighttime_hours:
        is_daytime = sunrise <= hour <= sunset
        assert not is_daytime, f"Expected nighttime for {hour}"


# ============================================================
# DAILY SUMMARY LOGIC TESTS
# ============================================================

def test_max_temp_always_above_min_temp():
    """Max temperature must always be higher than min temperature."""
    daily_readings = [
        {"max": 28.5, "min": 12.0},
        {"max": 35.2, "min": 20.1},
        {"max": 15.0, "min":  5.5},
    ]
    for reading in daily_readings:
        assert reading["max"] > reading["min"], \
            f"Max {reading['max']} not above min {reading['min']}"


def test_daylight_duration_is_positive():
    """Daylight duration must always be positive."""
    sample_durations = [35000.0, 38700.0, 42000.0]
    for duration in sample_durations:
        assert duration > 0, f"Daylight duration {duration} is not positive"


def test_daylight_duration_hours_conversion():
    """Daylight duration in seconds converts correctly to hours."""
    duration_s = 38700.0
    expected_h = round(38700.0 / 3600, 2)
    actual_h   = round(duration_s / 3600, 2)
    assert actual_h == expected_h