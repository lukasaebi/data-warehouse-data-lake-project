import argparse
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        raise Exception(f"Request failed with status code {response.status_code}")


def load_city_bboxes(filepath: str) -> list[dict]:
    """
    Loads the geocode information in bbox dormat for each city from the local filesystem.

    Args:
        filepath (str): The path to the file.
    """
    with open(filepath, "r") as f:
        return json.load(f)


def save_data(filepath: Path | str, data: dict) -> None:
    """
    Saves the data to the local filesystem in JSON format.

    Args:
        filepath (Path | str): The path to save the data.
        data (dict): The data to save.
    """
    if not isinstance(filepath, Path):
        filepath = Path(filepath)

    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


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
        filepath = config["filepath_base_output"] + f"/{day}/{city}_{start_date}_{end_date}.json"
        save_data(filepath=filepath, data=filtered_response)


def lambda_handler(event, context) -> None:
    with open(Path(__file__).absolute().parent / "config.yaml", "r") as f:
        config = yaml.safe_load(f)

    API_KEY = os.environ["HERE_API_KEY"]

    coordinates = load_city_bboxes(config["filepath_bboxes"])

    start_date = datetime.fromisoformat(event["start_date"]).replace(hour=6)
    end_date = datetime.fromisoformat(event["end_date"]).replace(hour=6)
    step = timedelta(days=1)

    current_date = start_date
    while current_date <= end_date:
        logger.info(f"Processing data for {current_date}")
        make_requests_for_one_day(current_date, coordinates, config, API_KEY)
        current_date += step


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=str, help="The start date in the format YYYY-MM-DD.")
    parser.add_argument("--end", type=str, help="The end date in the format YYYY-MM-DD.")
    return parser.parse_args()


if __name__ == "__main__":
    args = arg_parser()
    event = {"start_date": args.start, "end_date": args.end}

    lambda_handler(event, None)
