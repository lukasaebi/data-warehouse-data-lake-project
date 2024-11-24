import os
import requests
from datetime import datetime, timedelta
import json

# API Key (Insert your actual API key here)
API_KEY = "1b050c-bd22cf"

# Default historical date range
default_date_to = (datetime.now() - timedelta(days=5))
default_date_from = datetime.strptime("2023-12-01", "%Y-%m-%d")

# Local directories for storing data
ARRIVALS_DIR = r"C:\Users\carlo\Documents\aviations3\arrivals"
DEPARTURES_DIR = r"C:\Users\carlo\Documents\aviations3\departures"

# List of cities and their respective IATA codes
CITIES = [
    {"city": "zurich", "iata_codes": ["ZRH"]}
]

# Generate daily date segments within the date range
def generate_daily_segments(start_date, end_date):
    segments = []
    current_date = start_date
    while current_date <= end_date:
        segments.append((current_date.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")))
        current_date += timedelta(days=1)
    return segments

# Fetch arrival data for a given IATA code and date range
def fetch_arrival_data(iata_code, start_date, end_date):
    url = "https://aviation-edge.com/v2/public/flightsHistory"
    params = {
        "key": API_KEY,
        "code": iata_code,
        "type": "arrival",
        "date_from": start_date,
        "date_to": end_date
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching arrival data for {iata_code}: {e}")
        return None

# Fetch departure data for a given IATA code and date range
def fetch_departure_data(iata_code, start_date, end_date):
    url = "https://aviation-edge.com/v2/public/flightsHistory"
    params = {
        "key": API_KEY,
        "code": iata_code,
        "type": "departure",
        "date_from": start_date,
        "date_to": end_date
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching departure data for {iata_code}: {e}")
        return None

# Save data locally in the specified folder
def save_data_locally(data, folder, city, iata_code, date):
    city_folder = os.path.join(folder, city)
    os.makedirs(city_folder, exist_ok=True)
    file_path = os.path.join(city_folder, f"{iata_code}_{date}.json")
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Saved data to {file_path}")

# Main function for processing arrivals
def process_arrivals():
    date_segments = generate_daily_segments(default_date_from, default_date_to)

    for city_info in CITIES:
        city = city_info["city"]
        iata_codes = city_info["iata_codes"]

        for iata_code in iata_codes:
            for start_date, end_date in date_segments:
                data = fetch_arrival_data(iata_code, start_date, end_date)
                if data:
                    save_data_locally(data, ARRIVALS_DIR, city, iata_code, start_date)
                else:
                    print(f"No arrival data for {iata_code} in {city} on {start_date}")

# Main function for processing departures
def process_departures():
    date_segments = generate_daily_segments(default_date_from, default_date_to)

    for city_info in CITIES:
        city = city_info["city"]
        iata_codes = city_info["iata_codes"]

        for iata_code in iata_codes:
            for start_date, end_date in date_segments:
                data = fetch_departure_data(iata_code, start_date, end_date)
                if data:
                    save_data_locally(data, DEPARTURES_DIR, city, iata_code, start_date)
                else:
                    print(f"No departure data for {iata_code} in {city} on {start_date}")

# Entry point for processing arrivals and departures
def main():
    print("Processing arrivals...")
    process_arrivals()

    print("Processing departures...")
    process_departures()

if __name__ == "__main__":
    main()
