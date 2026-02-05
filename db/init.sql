-- OneWeather Database Initialization Script
-- Creates schema and initial tables for TimescaleDB

-- Create weather schema
CREATE SCHEMA IF NOT EXISTS weather;

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create forecast_model_runs table
CREATE TABLE weather.forecast_model_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    cycle_time TIMESTAMPTZ NOT NULL,
    forecast_hour INTEGER NOT NULL,
    resolution VARCHAR(20),
    data_path VARCHAR(500),
    file_size INTEGER,
    checksum VARCHAR(64),
    variables JSONB,
    status VARCHAR(20) DEFAULT 'ingested',
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    
    -- Ensure unique model runs
    UNIQUE(source, cycle_time, forecast_hour)
);

-- Create processed_forecasts table (will be converted to hypertable)
CREATE TABLE weather.processed_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_run_id UUID NOT NULL REFERENCES weather.forecast_model_runs(id),
    h3_index VARCHAR(20) NOT NULL,
    forecast_time TIMESTAMPTZ NOT NULL,
    variable VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20),
    confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable(
    'weather.processed_forecasts', 
    'forecast_time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Create observations table
CREATE TABLE weather.observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    station_id VARCHAR(10) NOT NULL,
    observation_time TIMESTAMPTZ NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    elevation FLOAT,
    temperature_c FLOAT,
    dewpoint_c FLOAT,
    pressure_hpa FLOAT,
    wind_speed_mps FLOAT,
    wind_direction_deg FLOAT,
    precipitation_mm FLOAT,
    visibility_m FLOAT,
    cloud_cover_oktas INTEGER,
    raw_text VARCHAR(500),
    quality_flag VARCHAR(20),
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert observations to hypertable
SELECT create_hypertable(
    'weather.observations', 
    'observation_time',
    chunk_time_interval => INTERVAL '30 days',
    if_not_exists => TRUE
);

-- Create evaluation_metrics table
CREATE TABLE weather.evaluation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_run_id UUID NOT NULL REFERENCES weather.forecast_model_runs(id),
    h3_index VARCHAR(20) NOT NULL,
    forecast_hour INTEGER NOT NULL,
    variable VARCHAR(50) NOT NULL,
    mae FLOAT,
    rmse FLOAT,
    bias FLOAT,
    correlation FLOAT,
    skill_score FLOAT,
    sample_size INTEGER,
    evaluation_period_start TIMESTAMPTZ,
    evaluation_period_end TIMESTAMPTZ,
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create blended_forecasts table
CREATE TABLE weather.blended_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    h3_index VARCHAR(20) NOT NULL,
    forecast_time TIMESTAMPTZ NOT NULL,
    variable VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20),
    confidence FLOAT,
    sources JSONB,
    source_weights JSONB,
    model_version VARCHAR(50),
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ
);

-- Convert blended_forecasts to hypertable
SELECT create_hypertable(
    'weather.blended_forecasts', 
    'forecast_time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Create indexes for performance
CREATE INDEX idx_processed_forecasts_h3_time 
ON weather.processed_forecasts (h3_index, forecast_time);

CREATE INDEX idx_processed_forecasts_variable 
ON weather.processed_forecasts (variable, forecast_time);

CREATE INDEX idx_observations_station_time 
ON weather.observations (station_id, observation_time);

CREATE INDEX idx_observations_location 
ON weather.observations (latitude, longitude);

CREATE INDEX idx_blended_forecasts_h3 
ON weather.blended_forecasts (h3_index, forecast_time);

CREATE INDEX idx_evaluation_metrics_h3_hour 
ON weather.evaluation_metrics (h3_index, forecast_hour);

-- Create materialized view for daily forecast accuracy
CREATE MATERIALIZED VIEW weather.daily_accuracy_summary AS
SELECT 
    DATE(calculated_at) as evaluation_date,
    variable,
    AVG(mae) as avg_mae,
    AVG(rmse) as avg_rmse,
    AVG(bias) as avg_bias,
    COUNT(*) as evaluation_count
FROM weather.evaluation_metrics
WHERE calculated_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(calculated_at), variable;

-- Refresh the materialized view daily
CREATE OR REPLACE FUNCTION weather.refresh_daily_accuracy()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW weather.daily_accuracy_summary;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create function to get forecast for a specific location
CREATE OR REPLACE FUNCTION weather.get_forecast_for_location(
    p_h3_index VARCHAR(20),
    p_start_time TIMESTAMPTZ,
    p_end_time TIMESTAMPTZ,
    p_variable VARCHAR(50) DEFAULT 'temperature'
)
RETURNS TABLE (
    forecast_time TIMESTAMPTZ,
    value FLOAT,
    unit VARCHAR(20),
    confidence FLOAT,
    sources JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bf.forecast_time,
        bf.value,
        bf.unit,
        bf.confidence,
        bf.sources
    FROM weather.blended_forecasts bf
    WHERE bf.h3_index = p_h3_index
        AND bf.variable = p_variable
        AND bf.forecast_time BETWEEN p_start_time AND p_end_time
    ORDER BY bf.forecast_time;
END;
$$ LANGUAGE plpgsql;

-- Create function to get observation history
CREATE OR REPLACE FUNCTION weather.get_observation_history(
    p_latitude FLOAT,
    p_longitude FLOAT,
    p_radius_km FLOAT DEFAULT 10.0,
    p_start_time TIMESTAMPTZ DEFAULT NOW() - INTERVAL '7 days',
    p_end_time TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
    station_id VARCHAR(10),
    observation_time TIMESTAMPTZ,
    distance_km FLOAT,
    temperature_c FLOAT,
    pressure_hpa FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.station_id,
        o.observation_time,
        -- Calculate distance using Haversine formula (simplified for small distances)
        111.045 * DEGREES(ACOS(
            LEAST(1.0, 
                SIN(RADIANS(p_latitude)) * SIN(RADIANS(o.latitude)) +
                COS(RADIANS(p_latitude)) * COS(RADIANS(o.latitude)) *
                COS(RADIANS(p_longitude - o.longitude))
            )
        )) as distance_km,
        o.temperature_c,
        o.pressure_hpa
    FROM weather.observations o
    WHERE o.observation_time BETWEEN p_start_time AND p_end_time
        AND 111.045 * DEGREES(ACOS(
            LEAST(1.0, 
                SIN(RADIANS(p_latitude)) * SIN(RADIANS(o.latitude)) +
                COS(RADIANS(p_latitude)) * COS(RADIANS(o.latitude)) *
                COS(RADIANS(p_longitude - o.longitude))
            )
        )) <= p_radius_km
    ORDER BY o.observation_time DESC, distance_km;
END;
$$ LANGUAGE plpgsql;

-- Insert initial configuration
INSERT INTO weather.forecast_model_runs (source, cycle_time, forecast_hour, resolution, status)
VALUES 
    ('gfs', NOW() - INTERVAL '6 hours', 0, '0p25', 'ingested'),
    ('gfs', NOW() - INTERVAL '12 hours', 0, '0p25', 'ingested'),
    ('hrrr', NOW() - INTERVAL '3 hours', 0, '3km', 'ingested')
ON CONFLICT DO NOTHING;

-- Create admin user for API access (password should be changed in production)
CREATE USER oneweather_api WITH PASSWORD 'change_this_password';
GRANT CONNECT ON DATABASE oneweather TO oneweather_api;
GRANT USAGE ON SCHEMA weather TO oneweather_api;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA weather TO oneweather_api;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA weather TO oneweather_api;

-- Create read-only user for analytics
CREATE USER oneweather_analytics WITH PASSWORD 'change_this_too';
GRANT CONNECT ON DATABASE oneweather TO oneweather_analytics;
GRANT USAGE ON SCHEMA weather TO oneweather_analytics;
GRANT SELECT ON ALL TABLES IN SCHEMA weather TO oneweather_analytics;

-- Output success message
SELECT 'OneWeather database initialized successfully!' as message;