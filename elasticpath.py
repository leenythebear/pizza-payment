import json
import os
from slugify import slugify

import redis
from dotenv import load_dotenv

import requests

_database = None


def get_token(client_id, client_secret, db):
    access_token = db.get('access_token')
    if not access_token:
        token_url = "https://useast.api.elasticpath.com/oauth/access_token"
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_info = response.json()
        time_to_expire = token_info['expires_in']
        access_token = token_info['access_token']
        db.set('access_token', access_token, ex=time_to_expire)
    else:
        access_token = access_token.decode()
    return access_token


def get_database_connection(host, port, password):
    global _database
    if _database is None:
        _database = redis.Redis(host=host, port=port, password=password)
    return _database


def load_file(token, image_url):
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    url = 'https://useast.api.elasticpath.com/v2/files'
    files = {
        'file_location': (None, image_url)
    }
    load_file_response = requests.post(url, headers=headers, files=files)
    load_file_response.raise_for_status()
    return load_file_response


def add_file_to_product(token, product_id, image_id):
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    json_data = {
        'data': {
            'type': 'file',
            'id': image_id,
        },
    }
    url = f'https://useast.api.elasticpath.com/pcm/products/{product_id}/relationships/main_image'
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()


def add_products(token):
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    with open("menu.json", "r") as my_file:
        menu_json = my_file.read()

    products = json.loads(menu_json)
    for product in products:
        json_data = {
            'data': {
                'type': 'product',
                'attributes': {
                    'name': product['name'],
                    'slug': slugify(product['name']),
                    'sku': slugify(product['name']),
                    'description': product['description'],
                    'manage_stock': False,
                    'price': [
                        {
                            'amount': product['price'],
                            'currency': 'RUB',
                            'includes_tax': True,
                        },
                    ],
                    'status': 'live',
                    'commodity_type': 'physical',
                },
            }
        }
        response = requests.post(
            'https://useast.api.elasticpath.com/pcm/products',
            headers=headers,
            json=json_data
        )
        response.raise_for_status()
        image_url = product['product_image']['url']
        product_id = response.json().get('data').get('id')
        image_id = (load_file(token, image_url)).json().get('data').get('id')

        add_file_to_product(token, product_id, image_id)
        return response


def create_flow(token):
    headers = {
    "Authorization": "Bearer {}".format(token),
    "Content-Type": "application/json",
    }
    json_data = {
        'data': {
            'type': 'flow',
            'name': 'Pizzeria_addresses',
            'slug': 'pizzeri-aaddresses',
            'description': 'Pizzeria addresses',
            'enabled': True,
        },
    }
    response = requests.post('https://useast.api.elasticpath.com/v2/flows', headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


def create_field(token, flow_id, field_name, field_type):
    url = 'https://useast.api.elasticpath.com/v2/fields'
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    data = {
        "data": {
            "type": "field",
            "name": field_name,
            "slug": slugify(field_name),
            "field_type": field_type,
            "description": field_name,
            "required": True,
            "enabled": True,
            "omit_null": False,
            "relationships": {
                "flow": {
                    "data": {
                        "type": "flow",
                        "id": flow_id
                    }
                }
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    load_dotenv()

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    db_host = os.environ["DATABASE_HOST"]
    db_port = os.environ["DATABASE_PORT"]
    db_password = os.environ["DATABASE_PASSWORD"]

    db = get_database_connection(db_host, db_port, db_password)
    token = get_token(client_id, client_secret, db)
    # flow_id = create_flow(token)
    print(777, create_field(token, '41bb069c-534b-4bb8-aa20-576c023aa189', 'Latitude', 'float'))

