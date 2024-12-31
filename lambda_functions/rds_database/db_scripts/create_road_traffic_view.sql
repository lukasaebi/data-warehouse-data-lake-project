"Materialized VIEW for average road traffic KPI's for each city per day"

CREATE MATERIALIZED VIEW road_traffic_v AS
SELECT
    CASE 
        WHEN city = 'Zürich' THEN 'Zurich'
        WHEN city = 'Frankfurt am Main' THEN 'Frankfurt'
        ELSE city
    END AS city,
    DATE(date) AS traffic_date,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY speed) AS median_speed,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY freeflow) AS median_freeflow,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY jamfactor) AS median_jam
FROM
    road_traffic
GROUP BY
    CASE 
        WHEN city = 'Zürich' THEN 'Zurich'
        WHEN city = 'Frankfurt am Main' THEN 'Frankfurt'
        ELSE city
    END,
    DATE(date)
ORDER BY
    city, traffic_date;

CREATE INDEX idx_road_traffic_city_date ON road_traffic_v (city, traffic_date);