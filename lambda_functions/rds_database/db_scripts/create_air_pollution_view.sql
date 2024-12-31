"Materialized View for air_pollution for each city hourly between 0600 to 0900"

CREATE MATERIALIZED VIEW air_pollution_v AS
SELECT
    place,
    date,
    air_quality_index,
    co,
    no,
    no2,
    o3,
    so2,
    pm2_5,
    pm10,
    nh3
FROM
    air_pollution_data;

CREATE INDEX idx_air_pollution_place_date ON air_pollution_v (place, date);