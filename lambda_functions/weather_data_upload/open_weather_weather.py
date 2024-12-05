import requests
import os
from dotenv import load_dotenv
import time
from datetime import datetime, timezone
import boto3
import json

with open("config.json", "r") as file:
    config = json.load(file)

#AWS S3 Client initialisieren
s3_client = boto3.client("s3")

# API-Schlüssel aus der .env-Datei laden

# Prüfen, ob der Code lokal ausgeführt wird
if not os.getenv("AWS_EXECUTION_ENV"):
    load_dotenv()  # Laden Sie .env nur lokal



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
    coordinates[city_name] = {"lat":city["lat"], "lon": city["lon"]}

# Berechne den Unix-Zeitstempel von vor 24 Stunden
#start = current_time - (7*86400)  # 24 Stunden = 86400 Sekunden

def fetch_latest_file_from_s3(s3_client, bucket_name):
    """
    Holt den neuesten Dateinamen aus dem S3-Bucket basierend auf dem Zeitstempel.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' not in response:
            print("Keine Dateien im Bucket gefunden.")
            return None
        
        # Neueste Datei anhand des letzten Modifizierungsdatums auswählen
        latest_file = max(response['Contents'], key=lambda x: x['LastModified'])
        return latest_file['Key']
    except Exception as e:
        print(f"Fehler beim Abrufen der Dateien aus S3: {e}")
        return None


def fetch_existing_data_from_s3(s3_client, bucket_name, key):
    """
    Lädt bestehende Daten aus einer Datei im S3-Bucket.
    """
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        existing_data = json.loads(response['Body'].read().decode('utf-8'))
        return existing_data
    except s3_client.exceptions.NoSuchKey:
        print("Keine bestehenden Daten gefunden.")
        return []
    except Exception as e:
        print(f"Fehler beim Abrufen bestehender Daten: {e}")
        return []


def determine_new_time_range(existing_data, current_time):
    """
    Bestimmt die fehlenden Zeitbereiche ab dem 1. Dezember 2023.
    """
    # Startzeitpunkt: 1. Dezember 2023, 00:00 UTC
    start_time = int(datetime(2023, 12, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())

    if not existing_data:
        # Keine bestehenden Daten vorhanden, Zeitbereiche ab dem Startzeitpunkt erstellen
        return [(start_time + week * 7 * 86400, start_time + (week + 1) * 7 * 86400 - 1) for week in range((current_time - start_time) // (7 * 86400) + 1)]
    
    # Bestimmen des jüngsten Zeitstempels aus den bestehenden Daten
    latest_timestamp = max(record['timestamp'] for record in existing_data)
    
    # Startzeitpunkt sicherstellen
    latest_timestamp = max(latest_timestamp, start_time)
    
    # Erstelle neue Zeitintervalle ab dem jüngsten Zeitstempel
    new_time_ranges = []
    one_week_in_seconds = 7 * 86400
    while latest_timestamp < current_time:
        start = latest_timestamp + 1  # Beginne direkt nach dem letzten Zeitstempel
        end = min(current_time, start + one_week_in_seconds - 1)
        new_time_ranges.append((start, end))
        latest_timestamp = end
    return new_time_ranges


def fetch_weather(coordinates, api_key, time_ranges):
    """
    Ruft Wetterdaten für die angegebenen Zeitbereiche ab und filtert nur Daten von 6:00 bis 9:00 Uhr UTC.
    """
    all_data = []  # Liste zum Speichern der Daten in flacher Struktur

    for place, coord in coordinates.items():
        lat = coord['lat']
        lon = coord['lon']

        for start, end in time_ranges:
            # API-Aufruf für historische Wetterdaten
            api_url = f"https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=day&start={start}&end={end}&appid={api_key}"

            try:
                response = requests.get(api_url)

                if response.status_code == 200:
                    data = response.json()
                    
                    # Iteriere durch jeden Dateneintrag und extrahiere relevante Felder
                    for entry in data.get('list', []):
                        observation_time = datetime.utcfromtimestamp(entry.get("dt"))
                        hour = observation_time.hour

                        # Filtere nur Daten zwischen 6:00 und 9:00 Uhr
                        if 6 <= hour < 10:
                            record = {
                                "place": place,
                                "latitude": lat,
                                "longitude": lon,
                                "timestamp": entry.get("dt"),
                                "date": observation_time.strftime('%Y-%m-%d %H:%M:%S'),
                                "temperature": entry["main"]["temp"],
                                "humidity": entry["main"]["humidity"],
                                "pressure": entry["main"]["pressure"],
                                "wind_speed": entry["wind"]["speed"],
                                "weather_main": entry["weather"][0]["main"],
                                "weather_description": entry["weather"][0]["description"]
                            }
                            # Füge den einzelnen Datensatz der flachen Datenstruktur hinzu
                            all_data.append(record)
                else:
                    # Fehlerhafte Anfragen debuggen
                    print(f"Fehlerhafte Anfrage für {place} ({lat}, {lon}). Statuscode: {response.status_code}, Antwort: {response.text}")

            except requests.exceptions.RequestException as e:
                print(f"Ein Fehler ist aufgetreten für {place} ({lat}, {lon}): {e}")

    # Debugging-Ausgabe: Anzahl der Datensätze
    print(f"Anzahl der neuen Datensätze abgerufen: {len(all_data)}")
    
    return all_data   # Gib die gesammelten Daten in flacher Struktur zurück



def lambda_handler(event, context):
    if not api_key or not S3_BUCKET_NAME:
        return {
            "statusCode": 500,
            "body": "API_KEY oder S3 Bucket Name fehlen"
        }

    # S3-Schlüssel definieren
    s3_key = "wetter/weather_data.json"
    
    # Bestehende Daten abrufen
    existing_data = fetch_existing_data_from_s3(s3_client, S3_BUCKET_NAME, s3_key)
    
    # Aktuelle Zeit bestimmen
    current_time = int(time.time())
    
    # Zeitintervalle bestimmen
    time_ranges = determine_new_time_range(existing_data, current_time)
    
    # Neue Daten abrufen
    new_data = fetch_weather(coordinates, api_key, time_ranges)
    
    # Neue Daten zu bestehenden Daten hinzufügen
    combined_data = existing_data + new_data

    #JSON-Daten in S3Bucket hochladen

    try:
        s3_client.put_object(
            Bucket = S3_BUCKET_NAME,
            Key = s3_key, 
            Body = json.dumps(combined_data), 
            ContentType = "application/json"
        )

        return {
            "statusCode":200, 
            'body': f'Daten erfolgreich in {s3_key} im Bucket {S3_BUCKET_NAME} gespeichert.'

        }
    
    except s3_client.exceptions.Boto3Error as e:
        return {
            'statusCode': 500,
            'body': f"Fehler beim Speichern der Daten in S3: {str(e)}"
        }


#data = fetch_weather(coordinates, api_key)

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
