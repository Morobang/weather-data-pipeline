-- ============================================================
-- BRONZE — RAW DAILY WEATHER
-- One row per municipality per fetch
-- The entire daily API response sits in raw_json untouched
-- Nothing is cleaned here — this is the raw landing zone
-- ============================================================

CREATE TABLE IF NOT EXISTS bronze.raw_weather_daily (
    id                  SERIAL PRIMARY KEY,
    municipality        VARCHAR(100)    NOT NULL,
    province            VARCHAR(100)    NOT NULL,
    municipality_type   VARCHAR(50)     NOT NULL,
    lat                 NUMERIC(9,6)    NOT NULL,
    lon                 NUMERIC(9,6)    NOT NULL,
    elevation_m         NUMERIC(8,2),
    fetched_at          TIMESTAMP       NOT NULL,
    weather_date        DATE            NOT NULL,
    raw_json            JSONB           NOT NULL
);