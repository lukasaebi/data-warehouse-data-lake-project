#!/usr/bin/env python
# coding: utf-8

# In[4]:


import requests
from dotenv import load_dotenv
import os

# In[5]:


# Lade Umgebungsvariablen aus der .env-Datei (z. B. API-Schlüssel)
load_dotenv()

# API-Schlüssel aus der .env-Datei laden
api_key = os.getenv('API_KEY')

# In[7]:


def fetch_coordinates(api_key, city_names):

    city_coordinates = []

    for cities in city_names:
        api_url = f"http://api.openweathermap.org/geo/1.0/direct?q={cities}&limit=5&appid={api_key}"
        
        try:
            # API GET-Request senden
            response = requests.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Daten der ersten Übereinstimmung nehmen (z.B. London, GB)
                    city_info = data[0]  # Nimmt den ersten Treffer
                    lat = city_info['lat']
                    lon = city_info['lon']
                    city_name = city_info["name"]

                    city_coordinates.append({
                        "city_name": city_name,
                        "lat": lat, 
                        "lon" : lon
                    })
                    
                    print(f"Stadt: {city_name}, Land: {city_info['country']}, Breitengrad: {lat}, Längengrad: {lon}")
                else:
                    print(f"Keine Daten für {cities} gefunden.")
            else:
                print(f"Fehlerhafte Anfrage für {cities}. Statuscode: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            print(f"Ein Fehler ist aufgetreten für {cities}: {e}")
    
    return city_coordinates

# Beispiel-Liste von Städten
city_names = ["London", "Paris", "Madrid", "Frankfurt", "Zurich", "Moscow", "Amsterdam", "Lisbon", "Rome", "Dublin", "Vienna"]

# In[8]:


cities_coordinates = fetch_coordinates(api_key, city_names)

# In[ ]:



