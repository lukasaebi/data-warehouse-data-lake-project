"Materialized VIEW main including all data"

CREATE MATERIALIZED VIEW master_view_v AS
WITH aggregated_flights AS (
    SELECT
        ca.city_name AS city,
        DATE(f.date) AS date,
        SUM(f.no_arrivals) AS no_arrivals,
        SUM(f.no_departures) AS no_departures,
        SUM(f.no_total_flights) AS no_total_flights
    FROM
        flights_v f
    JOIN
        city_airports_v ca
    ON
        f.airport_code = ca.iata_code
    GROUP BY
        ca.city_name, DATE(f.date)
),
max_air_pollution AS (
    SELECT
        place AS city,
        DATE(date) AS date,
        MAX(air_quality_index) AS air_quality_index,
        MAX(co) AS co,
        MAX(no) AS no,
        MAX(no2) AS no2,
        MAX(o3) AS o3,
        MAX(so2) AS so2,
        MAX(pm2_5) AS pm2_5,
        MAX(pm10) AS pm10,
        MAX(nh3) AS nh3
    FROM
        air_pollution_v
    GROUP BY
        place, DATE(date)
),
weather_max_time AS (
    SELECT DISTINCT ON (place, DATE(date))
        place AS city,
        DATE(date) AS date,
        weather_main
    FROM
        weather_v
    ORDER BY
        place, DATE(date), date DESC
)
SELECT
    af.city,
    ca.code_iso2_country,
    ca.name_country,
    af.date,
    af.no_arrivals,
    af.no_departures,
    af.no_total_flights,
    -- Custom group based on number of total flights
    CASE
        WHEN af.no_total_flights <= 50 THEN 1
        WHEN af.no_total_flights <= 100 THEN 2
        WHEN af.no_total_flights <= 150 THEN 3
        WHEN af.no_total_flights <= 200 THEN 4
        WHEN af.no_total_flights <= 250 THEN 5
        WHEN af.no_total_flights <= 300 THEN 6
        WHEN af.no_total_flights <= 350 THEN 7
        WHEN af.no_total_flights <= 400 THEN 8
        WHEN af.no_total_flights <= 450 THEN 9
        ELSE 10
    END AS custom_group,
    rt.normalized_avg_speed,
    rt.normalized_avg_freeflow,
    rt.normalized_avg_jam,
    ap.air_quality_index,
    ap.co,
    ap.no,
    ap.no2,
    ap.o3,
    ap.so2,
    ap.pm2_5,
    ap.pm10,
    ap.nh3,
    AVG(w.temperature) AS temperature,
    AVG(w.humidity) AS humidity,
    AVG(w.pressure) AS pressure,
    AVG(w.wind_speed) AS wind_speed,
    wm.weather_main
FROM
    aggregated_flights af
LEFT JOIN
    road_traffic_v rt
ON
    af.city = rt.city AND af.date = rt.traffic_date
LEFT JOIN
    max_air_pollution ap
ON
    af.city = ap.city AND af.date = ap.date
LEFT JOIN
    weather_v w
ON
    af.city = w.place AND af.date = DATE(w.date)
LEFT JOIN
    weather_max_time wm
ON
    af.city = wm.city AND af.date = wm.date
LEFT JOIN
    city_airports_v ca
ON
    af.city = ca.city_name
GROUP BY
    af.city, ca.code_iso2_country, ca.name_country, af.date, rt.normalized_avg_speed, rt.normalized_avg_freeflow, rt.normalized_avg_jam,
    af.no_arrivals, af.no_departures, af.no_total_flights, ap.air_quality_index, ap.co, ap.no, ap.no2, ap.o3, ap.so2, ap.pm2_5, ap.pm10, ap.nh3,
    wm.weather_main;

-- Create an index for efficient querying
CREATE INDEX idx_master_view_city_date ON master_view_v (city, date);