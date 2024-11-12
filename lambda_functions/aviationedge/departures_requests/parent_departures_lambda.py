import boto3
import json
import time

lambda_client = boto3.client('lambda')

# Define mapping of cities to Lambda functions
CITIES_TO_LAMBDAS = {
    "London_Part1": "london1_departure_lambda",
    "London_Part2": "london2_departure_lambda",
    "Paris": "paris_departure_lambda",
    "Amsterdam": "amsterdam_departure_lambda",
    "Madrid": "madrid_departure_lambda",
    "Frankfurt": "frankfurt_departure_lambda",
    "Rome": "rome_departure_lambda",
    "Moscow": "moscow_departure_lambda",
    "Lisbon": "lisbon_departure_lambda",
    "Dublin": "dublin_departure_lambda",
    "Vienna": "vienna_departure_lambda",
    "Zurich": "zurich_departure_lambda"
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
