import json
import os
import time

import boto3
import requests
import yaml


def get_city_geocode_info(query: str, ext: str, country_code: str, api_key: str) -> dict:
    """
    Retrieves the geo information of a city using the TomTom Geocoding API.
    Boundingbox coordinates of the cities must be extracted from the reponse
    for further use in the API.

    Args:
        query (str): The city name to search for.
        ext (str): The file extension of the response.
        country_code (str): The country code of the city.
        api_key (str): The TomTom API key.

    Returns:
        dict: The response from the API.
    """
    url = f"https://api.tomtom.com/search/2/geocode/{query}.{ext}"
    params = {
        "key": api_key,
        "countryCodeISO3": country_code,
        "entityTypeSet": "Municipality",
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Request failed with status code {response.status_code}")


def exctract_city_data(geocode_response: dict, city_name: str, country_code: str) -> dict:
    """Extracts data from the response which has `freeformAddress==city_name` and `countryCodeISO3==country_code`."""
    relevant_city_data = geocode_response.copy()
    results = []
    for result in geocode_response.get("results", []):
        if result["address"]["freeformAddress"] == city_name and result["address"]["countryCodeISO3"] == country_code:
            results.append(result)
    relevant_city_data["results"] = results
    return relevant_city_data


def request_geodata_for_multiple_cities(config: dict, api_key: str) -> list[dict]:
    """
    Requests the geo information for each city in the config file.

    Args:
        config (dict): The configuration file containing the cities and their country codes.
        api_key (str): The TomTom API key.

    Returns:
        list: A list of dictionaries containing the extracted geodata for each city.
    """
    extracted_cities = []
    for city, code in zip(config["cities"], config["country_codes"]):
        response = get_city_geocode_info(
            query=city,
            ext="json",
            country_code=code,
            api_key=api_key,
        )

        extracted_cities.append(exctract_city_data(response, city, code))
        time.sleep(0.25)
    return extracted_cities


def postprocess_api_response(data: list[dict]) -> dict:
    """Extracts only the relevant information from the api response data which are the city name and the bounding box."""
    return_data = {}
    for city in data:
        city_name = city["results"][0]["address"]["municipality"]
        boundingbox = city["results"][0]["boundingBox"]
        return_data[city_name] = boundingbox
    return return_data


def upload_data_to_s3(data: dict, bucket_name: str, key: str) -> None:
    """
    Uploads the data to the specified S3 bucket.

    Args:
        data (dict): The data to upload.
        bucket_name (str): The name of the S3 bucket.
        key (str): The key (object name) of the data.
    """
    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket_name, Key=key, Body=json.dumps(data, indent=4, ensure_ascii=False), ContentType="application/json"
    )


def lambda_handler(event, context):
    API_KEY = os.environ["TOMTOM_API_KEY"]
    S3_KEY = "geocode_data.json"
    BUCKET_NAME = "tomtom-api-data"

    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    response_data = request_geodata_for_multiple_cities(config, API_KEY)
    data = postprocess_api_response(response_data)

    upload_data_to_s3(data=data, bucket_name=BUCKET_NAME, key=S3_KEY)

    return {"statusCode": 200, "body": json.dumps(f"Data uploaded to S3 bucket '{BUCKET_NAME}' with key '{S3_KEY}'")}
