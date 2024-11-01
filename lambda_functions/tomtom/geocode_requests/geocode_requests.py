import json
import os
import requests
import boto3
from datetime import datetime, timezone

# AWS S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # TODO: how to write lambda function that makes api call and saves to S3
    
    # Some API request logic
    tomtom_url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point=52.41072,4.84239&key={TOMTOM_API_KEY}"
    
    response = requests.get(tomtom_url)
    
    data = response.json()
    timestamp = datetime.now(timezone.utc).isoformat()

    # Create a unique S3 key (object name)
    s3_key = f"tomtom_data_{timestamp}.json"

    # Upload the data to the S3 bucket
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(data),
        ContentType='application/json'
    )

    
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }