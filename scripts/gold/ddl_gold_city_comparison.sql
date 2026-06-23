-- ============================================================
-- GOLD — CITY COMPARISON
-- Latest reading for all 257 municipalities side by side
-- Shows current conditions across the whole country
-- This is the "dashboard view" — one row per municipality
-- ============================================================

CREATE OR REPLACE VIEW gold.city_comparison AS
SELECT
    h.municipality,
    h.province,
    h.municipality_type,
    h.weather_date,

    -- temperature
    d.temperature_max_c,
    d.temperature_min_c,
    d.temperature_range_c,

    -- hourly averages for the day
    ROUND(AVG(h.temperature_c)::NUMERIC, 2)         AS avg_temp_c,
    ROUND(AVG(h.humidity_pct)::NUMERIC, 2)          AS avg_humidity_pct,
    ROUND(AVG(h.windspeed_kmh)::NUMERIC, 2)         AS avg_windspeed_kmh,
    ROUND(AVG(h.cloudcover_pct)::NUMERIC, 2)        AS avg_cloudcover_pct,

    -- rainfall
    d.precipitation_sum_mm                          AS total_rain_mm,
    COUNT(*) FILTER (WHERE h.is_rainy = TRUE)       AS rainy_hours,

    -- uv
    MAX(h.uv_index)                                 AS max_uv_index,

    -- astronomy
    d.sunrise_at,
    d.sunset_at,
    d.daylight_duration_h,

    -- weather summary
    d.weathercode,
    d.weather_description,

    -- ranking within province
    RANK() OVER (
        PARTITION BY h.province, h.weather_date
        ORDER BY d.temperature_max_c DESC
    )                                               AS temp_rank_in_province,

    -- ranking nationally
    RANK() OVER (
        PARTITION BY h.weather_date
        ORDER BY d.temperature_max_c DESC
    )                                               AS temp_rank_national

FROM silver.weather_hourly h
JOIN silver.weather_daily d
    ON  h.municipality_id = d.municipality_id
    AND h.weather_date    = d.weather_date
GROUP BY
    h.municipality,
    h.province,
    h.municipality_type,
    h.weather_date,
    d.temperature_max_c,
    d.temperature_min_c,
    d.temperature_range_c,
    d.precipitation_sum_mm,
    d.sunrise_at,
    d.sunset_at,
    d.daylight_duration_h,
    d.weathercode,
    d.weather_description
ORDER BY
    h.weather_date DESC,
    temp_rank_national ASC;