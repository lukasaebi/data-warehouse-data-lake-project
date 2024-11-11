import requests
import os
from dotenv import load_dotenv
import time
import import_ipynb
from datetime import datetime, timezone
import boto3
import json
import yaml



with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

#AWS S3 Client initialisieren
s3_client = boto3.client("s3")

# API-Schlüssel aus der .env-Datei laden
cities_data = config["coordinates"]
api_key = config["API_KEY"]
S3_BUCKET_NAME = config["S3_BUCKET_NAME"]


coordinates = {}

for city in cities_data:
    city_name = city["city_name"]
    coordinates[city_name] = {"lat":city["lat"], "lon": city["lon"]}


def fetch_air_pollution(coordinates, api_key):
    # Aktuelles Datum in Unix-Timestamp umwandeln
    current_time = int(time.time())  # Aktueller Unix-Zeitstempel
    one_week_in_seconds = 7 * 86400
    all_data = []  # Liste zum Speichern der Daten in flacher Struktur

    for place, coord in coordinates.items():
        lat = coord['lat']
        lon = coord['lon']

        for week in range(52): 
            # Berechne den Start- und Endzeitpunkt für jede Woche
            start = current_time - ((week + 1) * one_week_in_seconds)
            end = current_time - (week * one_week_in_seconds)
        
            # API-Aufruf für historische Daten
            api_url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start}&end={end}&appid={api_key}"

            try:
                # API GET-Request senden
                response = requests.get(api_url)

                if response.status_code == 200:
                    data = response.json()

                    # Iteriere durch jede Stunde in den erhaltenen Daten
                    for entry in data.get("list", []):
                        observation = {
                            "place": place,
                            "latitude": lat,
                            "longitude": lon,
                            "week": week + 1,
                            "timestamp": entry.get("dt"),
                            "date": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(entry['dt'])),
                            "air_quality_index": entry["main"]["aqi"],
                            "components": entry["components"]
                        }
                        # Füge jede stündliche Beobachtung der flachen Struktur hinzu
                        all_data.append(observation)
                else:
                    print(f"Fehlerhafte Anfrage für {place} ({lat}, {lon}). Statuscode: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"Ein Fehler ist aufgetreten für {place} ({lat}, {lon}): {e}")

    return all_data  # Gib die flache Struktur zurück



def lambda_handler(event, context):
    #stell sicher, dass API-KEY und S3 Bucket gesetz sind
    if not api_key or not S3_BUCKET_NAME:
        return {
            "statusCode": 500, 
            "body": "API_KEY oder S3 Bucket Name fehlen"
        }

    #Daten abrufen
    data = fetch_air_pollution(coordinates, api_key)

    #Zeitstempel für Dateiname
    timestamp = datetime.now(timezone.utc).isoformat()

    #erstellen eines s3-schlüssels
    s3_key = f"air_pollution_data_{timestamp}.json"

    #JSON-Daten in S3Bucket hochladen

    try:
        s3_client.put_object(
            Bucket = S3_BUCKET_NAME,
            Key = s3_key, 
            Body = json.dumps(data), 
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
    


#polution_data = fetch_air_pollution(coordinates, api_key)


if __name__ == "__main__":
    result = lambda_handler({}, None)
    print(result)
