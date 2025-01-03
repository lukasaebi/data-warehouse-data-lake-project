import requests
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timezone
import boto3
import json

with open("config.json", "r") as file:
    config = json.load(file)

# AWS S3 Client initialize
s3_client = boto3.client("s3")

# Check whether the code is executed locally
if not os.getenv("AWS_EXECUTION_ENV"):
    load_dotenv()

api_key = os.getenv("API_KEY")
if not api_key:
    print("API_KEY konnte nicht geladen werden. Überprüfe die .env-Datei.")
else:
    print(f"API_KEY geladen: {api_key}")

cities_data = config["coordinates"]
S3_BUCKET_NAME = config["S3_BUCKET_NAME"]

coordinates = {}

for city in cities_data:
    city_name = city["city_name"]
    coordinates[city_name] = {"lat": city["lat"], "lon": city["lon"]}


def fetch_latest_file_from_s3(s3_client, bucket_name):
    """
    Fetches the latest file name from the S3 bucket based on the timestamp.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if "Contents" not in response:
            print("Keine Dateien im Bucket gefunden.")
            return None

        # Select the latest file based on the last modification date
        latest_file = max(response["Contents"], key=lambda x: x["LastModified"])
        return latest_file["Key"]
    except Exception as e:
        print(f"Fehler beim Abrufen der Dateien aus S3: {e}")
        return None


def fetch_existing_data_from_s3(s3_client, bucket_name, key):
    """
    Loads existing data from a file in the S3 bucket.
    """
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        existing_data = json.loads(response["Body"].read().decode("utf-8"))
        return existing_data
    except s3_client.exceptions.NoSuchKey:
        print("Keine bestehenden Daten gefunden.")
        return []
    except Exception as e:
        print(f"Fehler beim Abrufen bestehender Daten: {e}")
        return []


def determine_new_time_range(existing_data, current_time):
    """
    Determines the missing time ranges from December 1, 2023.
    """
    # Startingpoint: 1. Dezember 2023, 00:00 UTC
    start_time = int(datetime(2023, 12, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())

    if not existing_data:
        # No existing data available, create time ranges from the starting point
        return [
            (start_time + week * 7 * 86400, start_time + (week + 1) * 7 * 86400 - 1)
            for week in range((current_time - start_time) // (7 * 86400) + 1)
        ]

    # Determine the most recent timestamp from the existing data
    latest_timestamp = max(record["timestamp"] for record in existing_data)

    # Startingpoint sicherstellen
    latest_timestamp = max(latest_timestamp, start_time)

    # Create new time intervals from the most recent timestamp
    new_time_ranges = []
    one_week_in_seconds = 7 * 86400
    while latest_timestamp < current_time:
        start = latest_timestamp + 1
        end = min(current_time, start + one_week_in_seconds - 1)
        new_time_ranges.append((start, end))
        latest_timestamp = end
    return new_time_ranges


def fetch_weather(coordinates, api_key, time_ranges):
    """
    Retrieves weather data for the specified time ranges and only filters data from 6:00 to 9:00 UTC.
    """
    all_data = []

    for place, coord in coordinates.items():
        lat = coord["lat"]
        lon = coord["lon"]

        for start, end in time_ranges:
            # API call for historical weather data
            api_url = f"https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=day&start={start}&end={end}&appid={api_key}"

            try:
                response = requests.get(api_url)

                if response.status_code == 200:
                    data = response.json()

                    # Iterate through each data entry and extract relevant fields
                    for entry in data.get("list", []):
                        observation_time = datetime.utcfromtimestamp(entry.get("dt"))
                        hour = observation_time.hour

                        # Filter only data between 6:00 and 9:00 a.m.
                        if 6 <= hour < 10:
                            record = {
                                "place": place,
                                "latitude": lat,
                                "longitude": lon,
                                "timestamp": entry.get("dt"),
                                "date": observation_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "temperature": entry["main"]["temp"],
                                "humidity": entry["main"]["humidity"],
                                "pressure": entry["main"]["pressure"],
                                "wind_speed": entry["wind"]["speed"],
                                "weather_main": entry["weather"][0]["main"],
                                "weather_description": entry["weather"][0][
                                    "description"
                                ],
                            }
                            # Add the individual data set to the flat data structure
                            all_data.append(record)
                else:
                    # Debugging faulty requests
                    print(
                        f"Fehlerhafte Anfrage für {place} ({lat}, {lon}). Statuscode: {response.status_code}, Antwort: {response.text}"
                    )

            except requests.exceptions.RequestException as e:
                print(f"Ein Fehler ist aufgetreten für {place} ({lat}, {lon}): {e}")

    # Debugging output: Number of data records
    print(f"Anzahl der neuen Datensätze abgerufen: {len(all_data)}")

    return all_data  # Return the collected data in a flat structure


def lambda_handler(event, context):
    if not api_key or not S3_BUCKET_NAME:
        return {"statusCode": 500, "body": "API_KEY oder S3 Bucket Name fehlen"}

    # S3-Schlüssel definition
    s3_key = "wetter/weather_data.json"

    # Retrieve existing data
    existing_data = fetch_existing_data_from_s3(s3_client, S3_BUCKET_NAME, s3_key)

    # Determine current time
    current_time = int(time.time())

    # Determine time intervals
    time_ranges = determine_new_time_range(existing_data, current_time)

    # Retrieve new data
    new_data = fetch_weather(coordinates, api_key, time_ranges)

    # Add new data to existing data
    combined_data = existing_data + new_data

    # Upload JSON data to S3Bucket

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(combined_data),
            ContentType="application/json",
        )

        return {
            "statusCode": 200,
            "body": f"Daten erfolgreich in {s3_key} im Bucket {S3_BUCKET_NAME} gespeichert.",
        }

    except s3_client.exceptions.Boto3Error as e:
        return {
            "statusCode": 500,
            "body": f"Fehler beim Speichern der Daten in S3: {str(e)}",
        }


if __name__ == "__main__":
    print("Starte Skript...")
    try:
        print("Prüfe API_KEY...")
        if not api_key:
            raise ValueError("API_KEY fehlt. Überprüfe die .env-Datei.")
        print("API_KEY erfolgreich geladen.")

        print("Prüfe S3-Bucket...")
        if not S3_BUCKET_NAME:
            raise ValueError("S3_BUCKET_NAME fehlt in config.json.")

        print("Prüfe Koordinaten...")
        if not coordinates:
            raise ValueError("Keine Koordinaten in config.json gefunden.")

        print("Starte Lambda-Handler...")
        result = lambda_handler({}, None)
        print(f"Lambda-Handler abgeschlossen: {result}")
    except Exception as e:
        print(f"Fehler im Skript: {e}")
