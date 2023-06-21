import requests
from geopy import distance


def fetch_coordinates(api_key, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(
        base_url,
        params={
            "geocode": address,
            "apikey": api_key,
            "format": "json",
        },
    )
    response.raise_for_status()
    found_places = response.json()["response"]["GeoObjectCollection"][
        "featureMember"
    ]
    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant["GeoObject"]["Point"]["pos"].split(" ")
    return lon, lat


def get_coordinates(api_key, address):
    try:
        coords = fetch_coordinates(api_key, address)
    except (requests.exceptions.HTTPError, KeyError):
        coords = None

    if coords is None:
        return None
    else:
        lon, lat = coords
        return lat, lon


def get_distance(customer_coordinates, restaurant_coordinates):
    if all([*customer_coordinates, *restaurant_coordinates]):
        distance_between = round(
            distance.distance(customer_coordinates, restaurant_coordinates).km,
            1,
        )
        return distance_between
    return None
