import json
import os
from datetime import datetime, timedelta

import boto3
import requests
import yaml


def make_api_request(data: dict, api_key: str) -> dict:
    """
    Makes an API request to the HERE Traffic Flow API.

    Args:
        data (dict): The data to send in the request.
        api_key (str): The TomTom API key.

    Returns:
        dict: The response from the API.
    """
    url = f"https://data.traffic.hereapi.com/v7/flow?apiKey={api_key}"
    headers = {"Content-Type": "application/json"}

    response = requests.get(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Request failed with status code {response.status_code}")


def get_city_bboxes(client, bucket_name: str, filepath: str, out_path: str) -> None:
    """
    Extracts the geocode information in bbox dormat for each city from the S3 bucket.

    Args:
        client (boto3.client): The S3 client.
        bucket_name (str): The name of the S3 bucket.
        filepath (str): The path to the file in the S3 bucket.
        out_path (str): The path to save the extracted data.
    """
    obj = client.get_object(Bucket=bucket_name, Key=filepath)
    return json.loads(obj["Body"].read().decode("utf-8"))


def upload_data_to_s3(client: boto3.client, data: dict, bucket_name: str, key: str) -> None:
    """
    Uploads the data to the specified S3 bucket.

    Args:
        data (dict): The data to upload.
        bucket_name (str): The name of the S3 bucket.
        key (str): The key (object name) of the data.
    """
    client.put_object(
        Bucket=bucket_name, Key=key, Body=json.dumps(data, indent=4, ensure_ascii=False), ContentType="application/json"
    )


def lambda_handler(event, context):
    with open("lambda_functions/here/single_request/config.yaml", "r") as f:  # TODOD: change path to ./config.yaml
        config = yaml.safe_load(f)

    API_KEY = os.environ["TOMTOM_API_KEY"]
    BUCKET_NAME = config["bucket_name"]
    CITY = "Vienna"

    client = boto3.client("s3")
    # get_city_bboxes(client, BUCKET_NAME, config["filepath"], "geocode_data.json")
    with open("./downloads/geocode_data.json", "r") as f:  # TODO delete
        coordinates = json.load(f)

    # for city, timezone, summer_time_addition in zip(
    #     config["cities"], config["timezones"], config["summer_time_addition"], strict=True
    # ):
    timezone = config["timezones"][-1]  # TODO: functionize the start and end date retrieval
    summer_time_addition = config["summer_time_addition"][0]
    start_date = datetime(2024, 4, 1, 6 - timezone, 0, 0)
    end_date = start_date + timedelta(hours=3)
    if start_date >= datetime(*config["start_summer_time"]) and start_date <= datetime(*config["start_winter_time"]):
        start_date = start_date - timedelta(hours=summer_time_addition)
        end_date = end_date - timedelta(hours=summer_time_addition)
    start_date = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {
        "in": {
            "type": "bbox",
            "west": coordinates[CITY]["topLeftPoint"]["lon"],
            "south": coordinates[CITY]["btmRightPoint"]["lat"],
            "east": coordinates[CITY]["btmRightPoint"]["lon"],
            "north": coordinates[CITY]["topLeftPoint"]["lat"],
        },
        "locationReferencing": ["olr"],
        "minJamFactor": 0,
        "maxJamFactor": 9.9,
        "functionalClasses": [1, 2, 3],
        "startTime": start_date,
        "endTime": end_date,
    }
    response = make_api_request(data=data, api_key=API_KEY)
    key = f"traffic_volume/{CITY}_{start_date}_{end_date}.json"
    upload_data_to_s3(client, data=response, bucket_name=BUCKET_NAME, key=key)

    return {"statusCode": 200, "body": json.dumps(f"Data uploaded to S3 bucket '{BUCKET_NAME}' with key '{key}'")}


if __name__ == "__main__":
    lambda_handler(None, None)
