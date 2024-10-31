import requests


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
        'key': api_key,
        'countryCodeISO3': country_code,
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
    relevant_city_data["results"] = [result for result in geocode_response["results"] if result["address"]["freeformAddress"] == city_name and result["address"]["countryCodeISO3"] == country_code]
    return relevant_city_data


def request_info_for_each_city(config: dict, api_key: str) -> list:
    """Requests the geo information for each city in the config file."""
    extracted_cities = []
    for city, code in zip(config["cities"], config["country_codes"]):
        response = get_city_geocode_info(
            query=city,
            ext="json",
            country_code=code,
            api_key=api_key,
        )

        extracted_cities.append(exctract_city_data(response, city, code))
    return extracted_cities