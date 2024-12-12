-- Tabelle für Luftverschmutzungsdaten
CREATE TABLE air_pollution_data (
    id SERIAL PRIMARY KEY,
    place VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    timestamp BIGINT,
    date TIMESTAMP,
    air_quality_index INT,
    co FLOAT,
    no FLOAT,
    no2 FLOAT,
    o3 FLOAT,
    so2 FLOAT,
    pm2_5 FLOAT,
    pm10 FLOAT,
    nh3 FLOAT
);

-- Tabelle für Wetterdaten
CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    place VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    timestamp BIGINT,
    date TIMESTAMP,
    temperature FLOAT,
    humidity INT,
    pressure INT,
    wind_speed FLOAT,
    weather_main VARCHAR(255),
    weather_description VARCHAR(255)
);