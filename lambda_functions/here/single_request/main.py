import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import boto3
import requests
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

s3_client = boto3.client("s3")


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

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Request failed with status code {response.status_code}. {response.text}")


def load_city_bboxes(filepath: str) -> list[dict]:
    """
    Loads the geocode information in bbox dormat for each city from the local filesystem.

    Args:
        filepath (str): The path to the file.
    """
    with open(filepath, "r") as f:
        return json.load(f)


def download_s3_file(bucket_name: str, key: str, output_path: Path | str) -> None:
    """
    Download a file from S3 to a local path.

    Args:
        bucket_name (str): The name of the S3 bucket.
        key (str): The key of the file in the bucket.
        output_path (Path | str): The path to save the file to.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    s3_client.download_file(bucket_name, key, output_path)


def save_data(filepath: str, bucket_name: str, data: list[dict[str, Any]]) -> None:
    """
    Saves the data to the local filesystem in JSON format.

    Args:
        filepath (Path | str): The path to save the data.
        data (dict): The data to save.
    """
    json_data = json.dumps(data)
    response = s3_client.put_object(
        Bucket=bucket_name,
        Key=filepath,
        Body=json_data.encode("utf-8"),
        ContentType="application/json",
    )
    return response


def create_start_and_end_date(date_utc: datetime, timezone: int, summer_time_addition: int) -> tuple[str, str]:
    """
    Creates the start and end date for the API request.

    Args:
        date_utc (datetime): The current start date and time of when the data should be retrieved in UTC.
        timezone (int): The timezone of the city.
        summer_time_addition (int): The number of hours to add during summer time.
    """
    start_date = date_utc - timedelta(hours=timezone)
    end_date = start_date + timedelta(hours=3)
    if start_date >= datetime(2024, 3, 31) and start_date <= datetime(2024, 10, 27):
        start_date = start_date - timedelta(hours=summer_time_addition)
        end_date = end_date - timedelta(hours=summer_time_addition)
    start_date = start_date.strftime("%Y-%m-%dT%H:%M:%S")
    end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S")
    return start_date, end_date


def postprocess_api_response(data: dict):
    try:
        result = []
        for d in data["results"]:
            new_dict = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    filtered_dict = {k: v for k, v in value.items() if k != "subSegments"}
                    new_dict[key] = filtered_dict
                else:
                    new_dict[key] = value
            result.append(new_dict)
        return result
    except KeyError as e:
        raise KeyError("Key `results` not found in API response data.") from e


def make_requests_for_one_day(date: datetime, coordinates: dict, config: dict, API_KEY: str) -> None:
    """
    Makes API requests for a single day for all cities in the config.

    Args:
        date (datetime): The date for which to make the requests.
        coordinates (dict): The coordinates of the cities.
        config (dict): The configuration dictionary.
    """
    for city, timezone, summer_time_addition in zip(
        config["cities"], config["timezones"], config["summer_time_addition"], strict=True
    ):
        day = date.strftime("%Y-%m-%d")
        start_date, end_date = create_start_and_end_date(date, timezone, summer_time_addition)

        data = {
            "in": {
                "type": "bbox",
                "west": coordinates[city]["topLeftPoint"]["lon"],
                "south": coordinates[city]["btmRightPoint"]["lat"],
                "east": coordinates[city]["btmRightPoint"]["lon"],
                "north": coordinates[city]["topLeftPoint"]["lat"],
            },
            "locationReferencing": ["olr"],
            "minJamFactor": 0,
            "maxJamFactor": 9.9,
            "functionalClasses": [1, 2, 3],
            "startTime": start_date,
            "endTime": end_date,
        }
        response = make_api_request(data=data, api_key=API_KEY)
        filtered_response = postprocess_api_response(response)
        filepath = config["s3_basepath"] + f"/{day}/{city}_{start_date}_{end_date}.json"
        filepath = filepath.replace(":", "--")
        save_data(filepath=filepath, bucket_name=config["bucket_name"], data=filtered_response)


def lambda_handler(event, context):
    config_path = Path(__file__).absolute().parent / "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    API_KEY = os.environ["HERE_API_KEY"]
    logger.info("Config loaded.")

    download_s3_file(config["bucket_name"], config["geocode_filepath"], Path("/tmp/geocode_data.json"))
    logger.info("Geocode data downloaded.")
    coordinates = load_city_bboxes("/tmp/geocode_data.json")
    today = datetime.now()
    today = today.replace(hour=6, minute=0, second=0, microsecond=0)
    logger.info(f"Making requests for date {today.strftime('%Y-%m-%d')}.")
    make_requests_for_one_day(today, coordinates, config, API_KEY)

    return {
        "statusCode": 200,
        "body": json.dumps(
            f"Data succesfully requested and uploaded to S3 bucket '{config['bucket_name']}' at 'here/traffic_volume/{today.strftime('%Y-%m-%d')}'"
        ),
    }
