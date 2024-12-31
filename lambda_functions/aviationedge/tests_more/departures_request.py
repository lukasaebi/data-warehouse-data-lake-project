"""
This code is used to get all historical departure-flights from the api based on the airports in s3-bucket.
Restricitions for API-call: max 365 days before today / max 20k flights per request / max handling time abaout 15 min
"""

import json
import os
import requests
import boto3
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# S3 client API key
s3_client = boto3.client('s3')
api_key = os.getenv("API_KEY")

# Set date range
# Restrictions: max 365 before today
date_to = datetime.strptime("2024-10-31", "%Y-%m-%d")
date_from = datetime.strptime("2023-12-01", "%Y-%m-%d")

# Load cities and their IATA codes from config.yaml
def load_cities_from_config():
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
        return config.get("cities", {})

# Generate weekly date segments within the date range
# Restricitions: max 20k flights in one query available
def generate_weekly_segments(start_date, end_date):
    segments = []
    current_date = start_date
    while current_date < end_date:
        week_end_date = min(current_date + timedelta(days=6), end_date)
        segments.append((current_date.strftime("%Y-%m-%d"), week_end_date.strftime("%Y-%m-%d")))
        current_date = week_end_date + timedelta(days=1)
    return segments

# Fetch departure data from the API for a given IATA code and date range
def fetch_departure_data(iata_code, start_date, end_date):
    url = "https://aviation-edge.com/v2/public/flightsHistory"
    params = {
        "key": api_key,
        "code": iata_code,
        "type": "departure",
        "date_from": start_date,
        "date_to": end_date
    }
    
    # Error handling
    # Go to CloudWatch to monitor status of each request
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print(f"No data found for {iata_code} from {start_date} to {end_date}. Skipping this segment.")
            return None
        else:
            print(f"Error fetching departure data for {iata_code} from {start_date} to {end_date}: {e}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error for {iata_code} from {start_date} to {end_date}: {e}")
        return None

# Upload data to S3 bucket
# For each city one subfolder with corresponding iatacodes in it
# one file per week for each iatacode
def upload_departure_data_to_s3(data, bucket_name, s3_key):
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(data),
        ContentType='application/json'
    )

# Main Lambda handler for departures
def lambda_handler(event, context):
    cities = load_cities_from_config()
    target_bucket = "aviations3"
    
    # Parse IATA_CODES_BATCH from the event payload
    iata_codes_batch = event.get("IATA_CODES_BATCH", [])
    if not iata_codes_batch:
        print("No IATA_CODES_BATCH specified in the payload; processing all codes.")
    else:
        print(f"Processing only specified IATA codes: {iata_codes_batch}")
    
    for city, iata_codes in cities.items():
        # Filter IATA codes for this city based on IATA_CODES_BATCH
        filtered_iata_codes = [code for code in iata_codes if code in iata_codes_batch] if iata_codes_batch else iata_codes
        
        for iata_code in filtered_iata_codes:
            weekly_segments = generate_weekly_segments(date_from, date_to)
            for week_num, (start_date, end_date) in enumerate(weekly_segments, start=1):
                data = fetch_departure_data(iata_code, start_date, end_date)
                if data:
                    # Include iata_code in the S3 key
                    s3_key = f"departures/{city}/{iata_code}_week{week_num}.json"
                    upload_departure_data_to_s3(data, target_bucket, s3_key)
                    print(f"Stored data for {iata_code} in {s3_key}")
                else:
                    print(f"No data for {iata_code} in {city} from {start_date} to {end_date}")

    return {
        "statusCode": 200,
        "body": json.dumps("Weekly departure data stored in S3.")
    }
