"""
This code is used to get all airport information from the api based on the airports listed in config.yaml

"""

import json
import os
import requests
import boto3
import yaml
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

# API- and S3 config
s3_client = boto3.client('s3')
api_key = os.getenv("API_KEY")

# values based on config.yaml file
def load_config():
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    return config

# API request for iatacode in iatacodes
def api_request(iata_code):
    url = f"https://aviation-edge.com/v2/public/airportDatabase"
    params = {
        "key": api_key,
        "codeIataAirport": iata_code
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
    config = load_config()
    iatacodes = config["iatacodes"]
    bucket_name = config["bucket_name"]

    all_data = {}

    for iata_code in iatacodes:
        data = api_request(iata_code)
        all_data[iata_code] = data
    
    s3_key = f"aviation_edge_all_data.json"
    upload_to_s3(all_data, bucket_name, s3_key)

    return {
        "statusCode": 200,
        "body": json.dumps("Data stored in S3 for all cities!")
    }