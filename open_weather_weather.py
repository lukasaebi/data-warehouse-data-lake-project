import requests
import os
from dotenv import load_dotenv
import time
import import_ipynb


import open_weather_coordinates


coordinates = {}

for city in open_weather_coordinates.cities_coordinates:
    city_name = city["city_name"]
    coordinates[city_name] = {"lat":city["lat"], "lon": city["lon"]}




# Lade Umgebungsvariablen aus der .env-Datei (z. B. API-Schlüssel)
load_dotenv()

# API-Schlüssel aus der .env-Datei laden
api_key = os.getenv('API_KEY')


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


data = fetch_weather(coordinates, api_key)
