-- ============================================================
-- GOLD — DAILY SUMMARY
-- Average, max, min temp per municipality per day
-- Plus total rainfall and rainy hours
-- One row per municipality per day
-- ============================================================

CREATE OR REPLACE VIEW gold.daily_summary AS
SELECT
    h.municipality,
    h.province,
    h.municipality_type,
    h.weather_date,
    ROUND(AVG(h.temperature_c)::NUMERIC, 2)         AS avg_temp_c,
    MAX(h.temperature_c)                             AS max_temp_c,
    MIN(h.temperature_c)                             AS min_temp_c,
    ROUND(SUM(h.precipitation_mm)::NUMERIC, 2)       AS total_precipitation_mm,
    COUNT(*) FILTER (WHERE h.is_rainy = TRUE)        AS rainy_hours,
    ROUND(AVG(h.humidity_pct)::NUMERIC, 2)           AS avg_humidity_pct,
    ROUND(AVG(h.windspeed_kmh)::NUMERIC, 2)          AS avg_windspeed_kmh,
    MAX(h.windspeed_kmh)                             AS max_windspeed_kmh,
    ROUND(AVG(h.cloudcover_pct)::NUMERIC, 2)         AS avg_cloudcover_pct,
    MAX(h.uv_index)                                  AS max_uv_index,
    COUNT(*)                                         AS total_readings
FROM silver.weather_hourly h
GROUP BY
    h.municipality,
    h.province,
    h.municipality_type,
    h.weather_date;