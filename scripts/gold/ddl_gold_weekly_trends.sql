-- ============================================================
-- GOLD — WEEKLY TRENDS
-- 7-day rolling averages per municipality
-- Shows how temperature and rainfall trend over time
-- Only meaningful once you have 7+ days of data loaded
-- ============================================================

CREATE OR REPLACE VIEW gold.weekly_trends AS
SELECT
    d.municipality,
    d.province,
    d.municipality_type,
    d.weather_date,
    d.temperature_max_c,
    d.temperature_min_c,
    d.precipitation_sum_mm,

    -- 7-day rolling average temperature
    ROUND(AVG(d.temperature_max_c) OVER (
        PARTITION BY d.municipality
        ORDER BY d.weather_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )::NUMERIC, 2)                                  AS rolling_7d_avg_max_temp_c,

    ROUND(AVG(d.temperature_min_c) OVER (
        PARTITION BY d.municipality
        ORDER BY d.weather_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )::NUMERIC, 2)                                  AS rolling_7d_avg_min_temp_c,

    -- 7-day rolling total rainfall
    ROUND(SUM(d.precipitation_sum_mm) OVER (
        PARTITION BY d.municipality
        ORDER BY d.weather_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )::NUMERIC, 2)                                  AS rolling_7d_total_rain_mm,

    -- how many days out of 7 had rain
    SUM(CASE WHEN d.precipitation_sum_mm > 0 THEN 1 ELSE 0 END) OVER (
        PARTITION BY d.municipality
        ORDER BY d.weather_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )                                               AS rolling_7d_rainy_days,

    -- how many days of data we actually have for this window
    COUNT(*) OVER (
        PARTITION BY d.municipality
        ORDER BY d.weather_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )                                               AS days_in_window

FROM silver.weather_daily d
ORDER BY
    d.municipality,
    d.weather_date DESC;