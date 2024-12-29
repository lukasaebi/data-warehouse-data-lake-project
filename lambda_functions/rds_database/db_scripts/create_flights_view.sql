"Materialized View for all departures and arrivals for each city per day"

CREATE MATERIALIZED VIEW flights_v AS
WITH arrivals_per_hour AS (
    SELECT
        UPPER(arrival_iata) AS airport_code,
        DATE_TRUNC('hour', arrival_actual_time) AS date, -- Truncate to hour
        COUNT(*) AS no_arrivals
    FROM
        arrivals
    WHERE
        status = 'landed'
        AND DATE_PART('hour', arrival_actual_time) BETWEEN 6 AND 9
    GROUP BY
        arrival_iata, DATE_TRUNC('hour', arrival_actual_time)
),
departures_per_hour AS (
    SELECT
        UPPER(departure_iata) AS airport_code,
        DATE_TRUNC('hour', departure_actual_time) AS date, -- Truncate to hour
        COUNT(*) AS no_departures
    FROM
        departures
    WHERE
        status = 'active'
        AND DATE_PART('hour', departure_actual_time) BETWEEN 6 AND 9
    GROUP BY
        departure_iata, DATE_TRUNC('hour', departure_actual_time)
)
SELECT
    COALESCE(arrivals_per_hour.airport_code, departures_per_hour.airport_code) AS airport_code,
    COALESCE(arrivals_per_hour.date, departures_per_hour.date) AS date,
    COALESCE(no_arrivals, 0) AS no_arrivals,
    COALESCE(no_departures, 0) AS no_departures,
    COALESCE(no_arrivals, 0) + COALESCE(no_departures, 0) AS no_total_flights
FROM
    arrivals_per_hour
FULL OUTER JOIN
    departures_per_hour
ON
    arrivals_per_hour.airport_code = departures_per_hour.airport_code
    AND arrivals_per_hour.date = departures_per_hour.date;


CREATE INDEX idx_flights_airport_date ON flights_v (airport_code, date);