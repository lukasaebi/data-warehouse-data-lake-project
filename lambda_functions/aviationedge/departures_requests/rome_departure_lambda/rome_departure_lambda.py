import json
import os
import requests
import boto3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import yaml

load_dotenv()

# S3 client API key
s3_client = boto3.client('s3')
api_key = os.getenv("API_KEY")

# Set date range
date_to = datetime.strptime("2024-10-31", "%Y-%m-%d")
date_from = datetime.strptime("2023-12-01", "%Y-%m-%d")

def load_config():
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
        return config

# Generate weekly date segments within the date range
def generate_weekly_segments(start_date, end_date):
    segments = []
    current_date = start_date
    while current_date < end_date:
        week_end_date = min(current_date + timedelta(days=6), end_date)
        segments.append((current_date.strftime("%Y-%m-%d"), week_end_date.strftime("%Y-%m-%d")))
        current_date = week_end_date + timedelta(days=1)
    return segments

# Fetch departure data for a given IATA code and date range
def fetch_departure_data(iata_code, start_date, end_date):
    url = "https://aviation-edge.com/v2/public/flightsHistory"
    params = {
        "key": api_key,
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
        print(f"Error fetching data for {iata_code}: {e}")
        return None

# Upload data to S3
def upload_departure_data_to_s3(data, bucket_name, s3_key):
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(data),
        ContentType='application/json'
    )

# Main Lambda handler for the city
def lambda_handler(event, context):
    config = load_config()
    target_bucket = config["target_bucket"]
    iata_code = config["iata_code"]
    city = config["city"]
    
    weekly_segments = generate_weekly_segments(date_from, date_to)
    for week_num, (start_date, end_date) in enumerate(weekly_segments, start=1):
        data = fetch_departure_data(iata_code, start_date, end_date)
        if data:
            s3_key = f"departures/{city}/{iata_code}_week{week_num}.json"
            upload_departure_data_to_s3(data, target_bucket, s3_key)
            print(f"Stored data for {iata_code} in {s3_key}")
        else:
            print(f"No data for {iata_code} in {city} from {start_date} to {end_date}")

    return {
        "statusCode": 200,
        "body": json.dumps(f"Weekly departure data for {city} stored in S3.")
    }
