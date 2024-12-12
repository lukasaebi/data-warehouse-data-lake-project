import boto3
import psycopg2
import json
import os
from dotenv import load_dotenv
import logging
from psycopg2 import sql, extras  

load_dotenv()

# configure loggin
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

with open("config.json", "r") as config_file:
    config = json.load(config_file)

# Database access data
DB_CONFIG = {
    "host": config["DB_HOST"],
    "port": int(config["DB_PORT"]),
    "dbname": config["DB_NAME"],
    "user": config["DB_USER"],  
    "password": os.getenv("DB_PASSWORD")  
}

# S3-Bucket-Details
S3_BUCKET = "hslu-project-data"
AIR_POLLUTION_FILE = "pollution/air_pollution_data.json"
WEATHER_FILE = "wetter/weather_data.json"

def download_s3_file(bucket_name, key, local_path):
    """Lädt eine Datei von S3 herunter."""
    logging.info(f"Lade {key} aus S3-Bucket '{bucket_name}' herunter...")
    s3 = boto3.client('s3')
    try:
        s3.download_file(bucket_name, key, local_path)
        logging.info(f"{key} erfolgreich heruntergeladen.")
    except Exception as e:
        logging.error(f"Fehler beim Herunterladen von {key}: {e}")
        raise

def create_tables(conn):
    """
    Erstellt die benötigten Tabellen und fügt eindeutige Indizes hinzu.
    """
    with conn.cursor() as cur:
        air_pollution_table = """
        CREATE TABLE IF NOT EXISTS air_pollution_data (
            place VARCHAR(100),
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
            nh3 FLOAT,
            PRIMARY KEY (timestamp, place)  -- Kombinierter Primärschlüssel
        );
        """
        weather_table = """
        CREATE TABLE IF NOT EXISTS weather_data (
            place VARCHAR(100),
            latitude FLOAT,
            longitude FLOAT,
            timestamp BIGINT PRIMARY KEY,
            date TIMESTAMP,
            temperature FLOAT,
            humidity INT,
            pressure INT,
            wind_speed FLOAT,
            weather_main VARCHAR(50),
            weather_description VARCHAR(100),
            PRIMARY KEY (timestamp, place)  -- Kombinierter Primärschlüssel
        );
        """
        try:
            cur.execute(air_pollution_table)
            cur.execute(weather_table)
            conn.commit()
            logging.info("Tabellen erfolgreich erstellt (falls nicht vorhanden).")
        except Exception as e:
            conn.rollback()
            logging.error(f"Fehler beim Erstellen der Tabellen: {e}")
            raise

def insert_or_update_data(conn, table_name, columns, values, conflict_columns, update_columns):
    """
    Fügt Daten in eine Tabelle ein oder aktualisiert bestehende Einträge.
    """
    with conn.cursor() as cur:
        # create Update-clause
        update_clause = sql.SQL(", ").join(
            sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(col))
            for col in update_columns
        )
        # create Query 
        query = sql.SQL("""
            INSERT INTO {table} ({fields})
            VALUES %s
            ON CONFLICT ({conflict_fields}) DO UPDATE SET
            {updates}
        """).format(
            table=sql.Identifier(table_name),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            conflict_fields=sql.SQL(", ").join(map(sql.Identifier, conflict_columns)),
            updates=update_clause
        )
        try:
            extras.execute_values(cur, query, values)
            logging.info(f"Daten erfolgreich in die Tabelle '{table_name}' eingefügt oder aktualisiert.")
        except Exception as e:
            logging.error(f"Fehler beim Einfügen/Aktualisieren in die Tabelle '{table_name}': {e}")
            raise

def process_air_pollution_data(data):
    """Bereitet die air_pollution_data für das Einfügen in die Datenbank vor."""
    return [
        (
            entry["place"], entry["latitude"], entry["longitude"],
            entry["timestamp"], entry["date"], entry["air_quality_index"],
            entry["components"]["co"], entry["components"]["no"], entry["components"]["no2"],
            entry["components"]["o3"], entry["components"]["so2"],
            entry["components"]["pm2_5"], entry["components"]["pm10"],
            entry["components"]["nh3"]
        )
        for entry in data
    ]

def process_weather_data(data):
    """Bereitet die weather_data für das Einfügen in die Datenbank vor."""
    return [
        (
            entry["place"], entry["latitude"], entry["longitude"],
            entry["timestamp"], entry["date"], entry["temperature"],
            entry["humidity"], entry["pressure"], entry["wind_speed"],
            entry["weather_main"], entry["weather_description"]
        )
        for entry in data
    ]

def lambda_handler(event, context):
    # downlaod S3-Dateien 
    download_s3_file(S3_BUCKET, AIR_POLLUTION_FILE, "/tmp/air_pollution_data.json")
    download_s3_file(S3_BUCKET, WEATHER_FILE, "/tmp/weather_data.json")

    # laod JSON-file 
    with open("/tmp/air_pollution_data.json", "r") as f:
        air_pollution_data = json.load(f)
    with open("/tmp/weather_data.json", "r") as f:
        weather_data = json.load(f)

    # connect to database zur Datenbank 
    logging.info("Verbindung zur Datenbank herstellen...")
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # creat table 
        create_tables(conn)

        # Prepare and insert/update data
        air_pollution_values = process_air_pollution_data(air_pollution_data)
        insert_or_update_data(
            conn,
            "air_pollution_data",
            [
                "place", "latitude", "longitude", "timestamp", "date", "air_quality_index",
                "co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"
            ],
            air_pollution_values,
            conflict_columns=["timestamp", "place"],
            update_columns=[
                "latitude", "longitude", "date", "air_quality_index",
                "co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"
            ]
        )

        weather_values = process_weather_data(weather_data)
        insert_or_update_data(
            conn,
            "weather_data",
            [
                "place", "latitude", "longitude", "timestamp", "date", "temperature",
                "humidity", "pressure", "wind_speed", "weather_main", "weather_description"
            ],
            weather_values,
            conflict_columns=["timestamp", "place"],
            update_columns=[
                "latitude", "longitude", "date", "temperature",
                "humidity", "pressure", "wind_speed", "weather_main", "weather_description"
            ]
        )

        conn.commit()
        logging.info("Alle Daten erfolgreich eingefügt oder aktualisiert!")
    except Exception as e:
        conn.rollback()
        logging.error(f"Fehler: {e}")
    finally:
        conn.close()
        logging.info("Datenbankverbindung geschlossen.")

if __name__ == "__main__":
    print("Starte Skript...")
    try:
        # Checking the environment variables for the database
        print("Prüfe Datenbank-Konfiguration...")
        for key in ["host", "port", "dbname", "user", "password"]:
            if not DB_CONFIG.get(key):
                raise ValueError(f"Fehlende Datenbankkonfiguration: {key}. Überprüfe die .env-Datei.")
        print("Datenbank-Konfiguration erfolgreich geladen.")

        # Checking the S3 bucket
        print("Prüfe S3-Bucket...")
        if not S3_BUCKET:
            raise ValueError("S3_BUCKET fehlt. Überprüfe die Konfiguration.")
        print("S3-Bucket erfolgreich geladen.")

        # check S3 Bucketname
        print("Prüfe S3-Dateinamen...")
        if not AIR_POLLUTION_FILE or not WEATHER_FILE:
            raise ValueError("Einer der S3-Dateinamen fehlt. Überprüfe die Konfiguration.")
        print("S3-Dateinamen erfolgreich geladen.")

        # start Lambda-Handler
        print("Starte Lambda-Handler...")
        result = lambda_handler({}, None)  
        print(f"Lambda-Handler abgeschlossen: {result}")
    except Exception as e:
        print(f"Fehler im Skript: {e}")
