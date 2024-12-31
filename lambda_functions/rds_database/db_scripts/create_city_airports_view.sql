-- Create materialized view for city airports
CREATE MATERIALIZED VIEW city_airports_v AS
SELECT
    city_name,
    code_iso2_country,
    name_country,
    latitude,
    longitude,
    UNNEST(STRING_TO_ARRAY(iata_codes, ', ')) AS iata_code
FROM (
    SELECT
        city_name,
        STRING_AGG(code_iata_airport, ', ') AS iata_codes,
        code_iso2_country,
        name_country,
        MIN(latitude) AS latitude,
        MIN(longitude) AS longitude
    FROM
        airports
    GROUP BY
        city_name, code_iso2_country, name_country
) subquery;

-- Add index for faster lookup
CREATE INDEX idx_city_airports_city_iata ON city_airports_v (city_name, iata_code);