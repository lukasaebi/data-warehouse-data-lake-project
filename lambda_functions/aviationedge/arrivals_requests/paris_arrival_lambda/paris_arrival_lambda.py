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

# Set default historical date range
default_date_to = (datetime.now() - timedelta(days=5))
default_date_from = datetime.strptime("2023-12-01", "%Y-%m-%d")

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

# Generate single-day segment: This will be used for executing the function with eventbridge
def generate_daily_segment(date):
    return [(date.strftime("%Y-%m-%d"), date.strftime("%Y-%m-%d"))]

# Fetch arrival data for a given IATA code and date range
def fetch_arrival_data(iata_code, start_date, end_date):
    url = "https://aviation-edge.com/v2/public/flightsHistory"
    params = {
        "key": api_key,
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
        print(f"Error fetching data for {iata_code}: {e}")
        return None

# Upload data to S3
def upload_arrival_data_to_s3(data, bucket_name, s3_key):
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
    iata_codes = config["iata_code"]
    city = config["city"]
    
    # Ensure iata_codes is a list even if a single code is provided
    if isinstance(iata_codes, str):
        iata_codes = [iata_codes]
    
    # Determine the date range to fetch
    if "date_from" in event and "date_to" in event:
        # Historical fetch based on the provided date range
        date_from = datetime.strptime(event["date_from"], "%Y-%m-%d")
        date_to = datetime.strptime(event["date_to"], "%Y-%m-%d")
        date_segments = generate_weekly_segments(date_from, date_to)
    else:
        # Daily fetch for the last available day (today - 4 days): This will be used for executing the function with eventbridge
        today = datetime.now()
        fetch_date = today - timedelta(days=4)
        date_segments = generate_daily_segment(fetch_date)
    
    for iata_code in iata_codes:
        for start_date, end_date in date_segments:
            data = fetch_arrival_data(iata_code, start_date, end_date)
            if data:
                # Determine S3 key format
                if len(date_segments) == 1:
                    # Daily fetch: Save as {iata_code}_{date}.json
                    s3_key = f"aviations3/arrivals/{city}/{iata_code}_{start_date}.json"
                else:
                    # Weekly fetch: Save as {iata_code}_week{week_num}.json
                    week_num = date_segments.index((start_date, end_date)) + 1
                    s3_key = f"aviations3/arrivals/{city}/{iata_code}_week{week_num}.json"
                
                upload_arrival_data_to_s3(data, target_bucket, s3_key)
                print(f"Stored data for {iata_code} in {s3_key}")
            else:
                print(f"No data for {iata_code} in {city} from {start_date} to {end_date}")

    return {
        "statusCode": 200,
        "body": json.dumps(f"Arrival data for {city} stored in S3.")
    }