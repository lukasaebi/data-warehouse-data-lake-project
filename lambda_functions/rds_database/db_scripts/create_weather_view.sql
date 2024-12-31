"Materialized VIEW for weather data"

CREATE MATERIALIZED VIEW weather_v AS
SELECT
    place,
    date,
    temperature,
    humidity,
    pressure,
    wind_speed,
    weather_main
FROM
    weather_data;

CREATE INDEX idx_weather_place_date ON weather_v (place, date);