-- ============================================================
-- GOLD — HOTTEST MUNICIPALITIES
-- Ranks all municipalities by max temperature per day
-- Useful for seeing which areas are hottest on any given day
-- ============================================================

CREATE OR REPLACE VIEW gold.hottest_municipalities AS
SELECT
    d.weather_date,
    d.municipality,
    d.province,
    d.municipality_type,
    d.temperature_max_c,
    d.temperature_min_c,
    d.temperature_range_c,
    d.weathercode,
    d.weather_description,
    RANK() OVER (
        PARTITION BY d.weather_date
        ORDER BY d.temperature_max_c DESC
    )                                               AS temp_rank
FROM silver.weather_daily d
ORDER BY
    d.weather_date DESC,
    temp_rank ASC;