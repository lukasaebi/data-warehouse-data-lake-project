import requests
import os
from dotenv import load_dotenv
import time
import import_ipynb
from datetime import datetime, timezone
import boto3
import json


import open_weather_coordinates

#AWS S3 Client initialisieren
s3_client = boto3.client("s3")

coordinates = {}

for city in open_weather_coordinates.cities_coordinates:
    city_name = city["city_name"]
    coordinates[city_name] = {"lat":city["lat"], "lon": city["lon"]}




# Lade Umgebungsvariablen aus der .env-Datei (z. B. API-Schlüssel)
load_dotenv()

# API-Schlüssel aus der .env-Datei laden
api_key = os.getenv('API_KEY')

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


# Berechne den Unix-Zeitstempel von vor 24 Stunden
#start = current_time - (7*86400)  # 24 Stunden = 86400 Sekunden



def fetch_weather(coordinates, api_key):
    # Aktuelles Datum in Unix-Timestamp umwandeln
    current_time = int(time.time())  # Aktueller Unix-Zeitstempel
    one_week_in_seconds = 7 * 86400
    all_data = []  # Liste zum Speichern der Daten von allen Koordinaten

    for place, coord in coordinates.items():
        lat = coord['lat']
        lon = coord['lon']
        place_data = []  # Speichert die Daten für diesen Ort über mehrere Wochen

        for week in range(52): 
            # Berechne den Start- und Endzeitpunkt für jede Woche
            start = current_time - ((week + 1) * one_week_in_seconds)
            end = current_time - (week * one_week_in_seconds)
        
            # API-Aufruf für historische Daten
            api_url = f"https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=day&start={start}&end={end}&appid={api_key}"

            try:
                # API GET-Request senden
                response = requests.get(api_url)

                if response.status_code == 200:
                    data = response.json()
                    print(f"API Response for Place {place} ({lat}, {lon}) Week {week+1}:", data)
                    place_data.append(data)  # Wochendaten zu place_data hinzufügen
                else:
                    print(f"Fehlerhafte Anfrage für {place} ({lat}, {lon}). Statuscode: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"Ein Fehler ist aufgetreten für {place} ({lat}, {lon}): {e}")
        
        all_data.append({place: place_data})  # Wochenweise Daten für den Ort hinzufügen

    return all_data  # Gib die gesammelten Daten zurück


def lambda_handler(event, context):
    #stell sicher, dass API-KEY und S3 Bucket gesetz sind
    if not api_key or not S3_BUCKET_NAME:
        return {
            "statusCode": 500, 
            "body": "API_KEY oder S3 Bucket Name fehlen"
        }

    #Daten abrufen
    data = fetch_weather(coordinates, api_key)

    #Zeitstempel für Dateiname
    timestamp = datetime.now(timezone.utc).isoformat()

    #erstellen eines s3-schlüssels
    s3_key = f"weather_data_{timestamp}.json"

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


#data = fetch_weather(coordinates, api_key)
