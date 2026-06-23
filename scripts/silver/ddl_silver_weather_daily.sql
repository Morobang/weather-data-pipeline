-- ============================================================
-- SILVER — WEATHER DAILY
-- One row per municipality per day
-- Exploded and cleaned from bronze.raw_weather_daily
-- 257 municipalities × 1 day = 257 rows per day
-- ============================================================

CREATE TABLE IF NOT EXISTS silver.weather_daily (
    id                  SERIAL PRIMARY KEY,
    municipality_id     INT             NOT NULL REFERENCES silver.dim_municipalities(id),
    municipality        VARCHAR(100)    NOT NULL,
    province            VARCHAR(100)    NOT NULL,
    municipality_type   VARCHAR(50)     NOT NULL,
    weather_date        DATE            NOT NULL,
    elevation_m         NUMERIC(8,2),
    temperature_max_c   NUMERIC(5,2),
    temperature_min_c   NUMERIC(5,2),
    temperature_range_c NUMERIC(5,2)    GENERATED ALWAYS AS (temperature_max_c - temperature_min_c) STORED,
    precipitation_sum_mm NUMERIC(7,2),
    windspeed_max_kmh   NUMERIC(6,2),
    sunrise_at          TIMESTAMP,
    sunset_at           TIMESTAMP,
    daylight_duration_s NUMERIC(10,2),
    daylight_duration_h NUMERIC(5,2)    GENERATED ALWAYS AS (ROUND((daylight_duration_s / 3600)::NUMERIC, 2)) STORED,
    weathercode         INTEGER,
    weather_description VARCHAR(100),
    loaded_at           TIMESTAMP       DEFAULT NOW(),

    -- no duplicate readings per municipality per day
    UNIQUE (municipality_id, weather_date)
);

-- ============================================================
-- INDEXES
-- ============================================================

-- filter by date
CREATE INDEX IF NOT EXISTS idx_weather_daily_date
    ON silver.weather_daily (weather_date);

-- filter by province
CREATE INDEX IF NOT EXISTS idx_weather_daily_province
    ON silver.weather_daily (province);

-- filter by municipality
CREATE INDEX IF NOT EXISTS idx_weather_daily_municipality
    ON silver.weather_daily (municipality_id);