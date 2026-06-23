-- ============================================================
-- SILVER — WEATHER HOURLY
-- One row per municipality per hour
-- Exploded and cleaned from bronze.raw_weather_hourly
-- 257 municipalities × 24 hours = 6,168 rows per day
-- ============================================================

CREATE TABLE IF NOT EXISTS silver.weather_hourly (
    id                  SERIAL PRIMARY KEY,
    municipality_id     INT             NOT NULL REFERENCES silver.dim_municipalities(id),
    municipality        VARCHAR(100)    NOT NULL,
    province            VARCHAR(100)    NOT NULL,
    municipality_type   VARCHAR(50)     NOT NULL,
    recorded_at         TIMESTAMP       NOT NULL,
    weather_date        DATE            NOT NULL,
    temperature_c       NUMERIC(5,2),
    precipitation_mm    NUMERIC(6,2),
    windspeed_kmh       NUMERIC(6,2),
    humidity_pct        INTEGER,
    cloudcover_pct      INTEGER,
    visibility_m        NUMERIC(10,2),
    uv_index            NUMERIC(4,2),
    surface_pressure_hpa NUMERIC(7,2),
    is_rainy            BOOLEAN         GENERATED ALWAYS AS (precipitation_mm > 0) STORED,
    is_daytime          BOOLEAN,
    loaded_at           TIMESTAMP       DEFAULT NOW(),

    -- no duplicate readings per municipality per hour
    UNIQUE (municipality_id, recorded_at)
);

-- ============================================================
-- INDEXES — speeds up common queries
-- ============================================================

-- filter by date
CREATE INDEX IF NOT EXISTS idx_weather_hourly_date
    ON silver.weather_hourly (weather_date);

-- filter by province
CREATE INDEX IF NOT EXISTS idx_weather_hourly_province
    ON silver.weather_hourly (province);

-- filter by municipality
CREATE INDEX IF NOT EXISTS idx_weather_hourly_municipality
    ON silver.weather_hourly (municipality_id);