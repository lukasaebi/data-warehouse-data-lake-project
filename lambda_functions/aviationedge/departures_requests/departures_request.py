"""
This code is used to get all historical departure-flights from the api based on the airports in s3-bucket

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

# date range
date_to = datetime.now() - timedelta(days=1)
date_from = date_to - timedelta(days=330)


# Load iata codes from JSON
def load_iatacodes_from_config():
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
        return config.get("iatacodes", [])


# Generate 31-day segments within the date range - monthly
def generate_monthly_segments(start_date, end_date):
    segments = []
    current_date = start_date
    while current_date < end_date:
        # Get the last day of the month
       month_end_date = min((current_date.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1), end_date)
       segments.append((current_date.strftime("%Y-%m-%d"), month_end_date.strftime("%Y-%m-%d")))
       current_date = month_end_date + timedelta(days=1)
    return segments

# departure data for a specific IATA code
def fetch_departure_data(iata_code, start_date, end_date):
    url = "https://aviation-edge.com/v2/public/flightsHistory"
    params = {
        "key": api_key,
        "code": iata_code,
        "type": "departure",
        "date_from": start_date,
        "date_to": end_date
    }
    
    #Error handling useful
    #sometimes no data is available. if this is the case, return none and skip to next iata code
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

# Upload departure data to S3 bucket
def upload_departure_data_to_s3(data, bucket_name, s3_key):
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(data),
        ContentType='application/json'
        )

# Main Lambda function
def lambda_handler(event, context):
    iatacodes = load_iatacodes_from_config()
    target_bucket = "aviations3-departures"
    
    for iata_code in iatacodes:
        # Generate monthly segments within the date range
        date_segments = generate_monthly_segments(date_from, date_to)

        for start_date, end_date in date_segments:
            departure_data = fetch_departure_data(iata_code, start_date, end_date)

            if departure_data:
                # Define S3 key based on IATA code, year, and month
                start_month = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y%m")
                s3_key = f"aviation_edge_departure_{iata_code}_{start_month}.json"

                # Upload data for each IATA code and month to S3
                upload_departure_data_to_s3(departure_data, target_bucket, s3_key)
            else:
                print(f"Skipping {iata_code} for {start_date} to {end_date} due to missing data.")

        # Log progress for each IATA code
        print(f"Completed data fetch and storage for {iata_code}")

    return {
        "statusCode": 200,
        "body": json.dumps("Monthly departure data stored in S3 for all IATA codes.")
    }