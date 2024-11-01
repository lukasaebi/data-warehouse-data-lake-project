import json
import os
import requests
import boto3
from datetime import datetime, timezone

# AWS S3 client
s3_client = boto3.client('s3')

def my_lambda_function(text: str) -> str:
    return "______" + text + "______"

def lambda_handler(event: dict, context):
    text = event['text']
    message = my_lambda_function(text)
    return {
        'statusCode': 200,
        'body': message
    }

def lambda_handler_(event: dict, context):
    # TODO: how to write lambda function that makes api call and saves to S3
    
    # Some API request logic
    tomtom_url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point=52.41072,4.84239&key="
    
    response = requests.get(tomtom_url)
    
    data = response.json()
    timestamp = datetime.now(timezone.utc).isoformat()

    # Create a unique S3 key (object name)
    s3_key = f"tomtom_data_{timestamp}.json"

    # Upload the data to the S3 bucket
    s3_client.put_object(
        Bucket="",
        Key=s3_key,
        Body=json.dumps(data),
        ContentType='application/json'
    )

    
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }