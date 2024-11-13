"""
This code is used to get all historical arrival-flights from the api based on the airports in s3-bucket.
Restricitions for API-call: max 365 days before today / max 20k flights per request / max handling time about 15 min
"""

import boto3
import json
import time

lambda_client = boto3.client('lambda')

# Define mapping of cities to Lambda functions
CITIES_TO_LAMBDAS = {
    "London_Part1": "london1_arrival_lambda",
    "London_Part2": "london2_arrival_lambda",
    "Paris": "paris_arrival_lambda",
    "Amsterdam": "amsterdam_arrival_lambda",
    "Madrid": "madrid_arrival_lambda",
    "Frankfurt": "frankfurt_arrival_lambda",
    "Rome": "rome_arrival_lambda",
    "Moscow": "moscow_arrival_lambda",
    "Lisbon": "lisbon_arrival_lambda",
    "Dublin": "dublin_arrival_lambda",
    "Vienna": "vienna_arrival_lambda",
    "Zurich": "zurich_arrival_lambda"
}

def lambda_handler(event, context):
    # Optional: specify cities in the event payload
    cities = event.get("CITIES", CITIES_TO_LAMBDAS.keys())

    # Iterate over each city and invoke corresponding Lambda
    for city in cities:
        function_name = CITIES_TO_LAMBDAS.get(city)
        if not function_name:
            print(f"No Lambda function found for city {city}")
            continue
        
        print(f"Invoking Lambda function for city: {city}")
        payload = json.dumps({"IATA_CODES_BATCH": city})

        # Invoke the Lambda function asynchronously
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # Async invocation
            Payload=payload,
        )

        # Add delay if needed to avoid throttling
        time.sleep(0.5)

    return {
        "statusCode": 200,
        "body": json.dumps(f"Invoked Lambda functions for cities: {cities}")
    }