"""
This code fetches all the historical data and stores it localy. The folders containing the historical files can then be uploaded once in AWS S3 environment.
This procedures handles API request respectively AWS limitations.
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv # type: ignore
import json

load_dotenv()

# API Key (Insert your actual API key here)
API_KEY = os.getenv("API_KEY")

# Default historical date range
default_date_to = (datetime.now() - timedelta(days=5))
default_date_from = datetime.strptime("2023-12-01", "%Y-%m-%d")

# Local directory for storing departure data
DEPARTURES_DIR = os.path.join("aviations3", "departures")

# List of cities and their respective IATA codes
CITIES = [
    {"city": "amsterdam", "iata_codes": ["AMS"]},
    {"city": "dublin", "iata_codes": ["DUB"]},
    {"city": "frankfurt", "iata_codes": ["FRA", "HHN"]},
    {"city": "lisbon", "iata_codes": ["LIS"]},
    {"city": "london1", "iata_codes": ["LCY", "LGW", "LHR"]},
    {"city": "london2", "iata_codes": ["LTN", "SEN", "STN"]},
    {"city": "madrid", "iata_codes": ["MAD"]},
    {"city": "moscow", "iata_codes": ["DME", "SVO", "VKO"]},
    {"city": "paris", "iata_codes": ["BVA", "CDG", "ORY"]},
    {"city": "rome", "iata_codes": ["FCO"]},
    {"city": "vienna", "iata_codes": ["VIE"]}
]

# Generate 6-day date segments within the date range
def generate_weekly_segments(start_date, end_date):
    segments = []
    current_date = start_date
    while current_date <= end_date:
        segment_end_date = min(current_date + timedelta(days=5), end_date)
        segments.append((current_date.strftime("%Y-%m-%d"), segment_end_date.strftime("%Y-%m-%d")))
        current_date = segment_end_date + timedelta(days=1)
    return segments

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
def save_data_locally(data, folder, city, iata_code, date_range):
    city_folder = os.path.join(folder, city)
    os.makedirs(city_folder, exist_ok=True)
    file_path = os.path.join(city_folder, f"{iata_code}_{date_range}.json")
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Saved data to {file_path}")

# Main function for processing departures
def process_departures():
    date_segments = generate_weekly_segments(default_date_from, default_date_to)

    for city_info in CITIES:
        city = city_info["city"]
        iata_codes = city_info["iata_codes"]

        for iata_code in iata_codes:
            for start_date, end_date in date_segments:
                data = fetch_departure_data(iata_code, start_date, end_date)
                if data:
                    date_range = f"{start_date}_to_{end_date}"
                    save_data_locally(data, DEPARTURES_DIR, city, iata_code, date_range)
                else:
                    print(f"No departure data for {iata_code} in {city} from {start_date} to {end_date}")

# Entry point for processing departures
def main():
    process_departures()

if __name__ == "__main__":
    main()

