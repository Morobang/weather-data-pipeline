-- ============================================================
-- GOLD — PROVINCE SUMMARY
-- Same as daily summary but grouped by province
-- One row per province per day
-- Useful for comparing provinces against each other
-- ============================================================

CREATE OR REPLACE VIEW gold.province_summary AS
SELECT
    h.province,
    h.weather_date,
    COUNT(DISTINCT h.municipality)                   AS total_municipalities,
    ROUND(AVG(h.temperature_c)::NUMERIC, 2)         AS avg_temp_c,
    MAX(h.temperature_c)                             AS max_temp_c,
    MIN(h.temperature_c)                             AS min_temp_c,
    ROUND(SUM(h.precipitation_mm)::NUMERIC, 2)       AS total_precipitation_mm,
    ROUND(AVG(h.humidity_pct)::NUMERIC, 2)           AS avg_humidity_pct,
    ROUND(AVG(h.windspeed_kmh)::NUMERIC, 2)          AS avg_windspeed_kmh,
    MAX(h.windspeed_kmh)                             AS max_windspeed_kmh,
    ROUND(AVG(h.cloudcover_pct)::NUMERIC, 2)         AS avg_cloudcover_pct,
    MAX(h.uv_index)                                  AS max_uv_index,
    COUNT(*) FILTER (WHERE h.is_rainy = TRUE)        AS total_rainy_readings,
    COUNT(*)                                         AS total_readings
FROM silver.weather_hourly h
GROUP BY
    h.province,
    h.weather_date;