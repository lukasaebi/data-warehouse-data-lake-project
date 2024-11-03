import json
import os
import requests
import boto3
import yaml
from datetime import datetime, timezone



# API- and S3 config
s3_client = boto3.client('s3')
api_key = os.getenv("API_KEY")
bucket_name = os.getenv("S3_BUCKET")

# cities based on config.yaml file
def load_config():
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    return config.get("cities", [])

# API request for city in cities
def api_data(city):
    url = "https://aviation-edge.com/v2/public/autocomplete"
    params = {
        "key": api_key,
        "city": city
    }
    
    response = requests.get(url, params=params)
    return response.json()

# put data in s3 bucket
def upload_to_s3(data, bucket_name, s3_key):
    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(data),
        ContentType='application/json'
    )

# main lambda function
def lambda_handler(event, context):
    cities = load_config()

    for city in cities:
        data = api_data(city)

        timestamp = datetime.now(timezone.utc).isoformat()
        s3_key = f"aviation_edge_data_{city.replace(' ', '_')}_{timestamp}.json"

        upload_to_s3(data, bucket_name, s3_key)

        return {
            "statusCode": 200,
            "body": json.dumps("Data stored in S3 for all cities!")
        }