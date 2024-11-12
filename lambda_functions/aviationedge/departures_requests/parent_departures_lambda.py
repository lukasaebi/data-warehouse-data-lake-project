import boto3
import json
import time

lambda_client = boto3.client('lambda')

# Define mapping of cities to Lambda functions
CITIES_TO_LAMBDAS = {
    "London_Part1": "departures_LondonPart1",
    "London_Part2": "departures_LondonPart2",
    "Paris": "departures_Paris",
    "Amsterdam": "departures_Amsterdam",
    "Madrid": "departures_nMadrid",
    "Frankfurt": "departures_Frankfurt",
    "Rome": "departures_Rome",
    "Moscow": "departures_Moscow",
    "Lisbon": "departures_Lisbon",
    "Dublin": "departures_Dublin",
    "Vienna": "departures_Vienna",
    "Zurich": "departures_Zurich",
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
