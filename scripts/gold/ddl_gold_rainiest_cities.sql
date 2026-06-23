-- ============================================================
-- GOLD — RAINIEST MUNICIPALITIES
-- Ranks all municipalities by total precipitation per day
-- Only shows municipalities that actually had rainfall
-- Useful for seeing where it rained and how much
-- ============================================================

CREATE OR REPLACE VIEW gold.rainiest_municipalities AS
SELECT
    d.weather_date,
    d.municipality,
    d.province,
    d.municipality_type,
    d.precipitation_sum_mm,
    d.temperature_max_c,
    d.temperature_min_c,
    d.windspeed_max_kmh,
    d.weathercode,
    d.weather_description,
    RANK() OVER (
        PARTITION BY d.weather_date
        ORDER BY d.precipitation_sum_mm DESC
    )                                               AS rain_rank
FROM silver.weather_daily d
WHERE d.precipitation_sum_mm > 0
ORDER BY
    d.weather_date DESC,
    rain_rank ASC;