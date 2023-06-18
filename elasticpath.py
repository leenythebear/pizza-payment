import json
import os
from slugify import slugify

import redis
from dotenv import load_dotenv

import requests

_database = None


def get_token(client_id: str, client_secret: str, db: redis.Redis) -> str:
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


def get_products(token):
    products_url = "https://useast.api.elasticpath.com/pcm/products"
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    response = requests.get(products_url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_product_by_id(product_id, token):
    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = requests.get(
        f"https://useast.api.elasticpath.com/catalog/products/{product_id}",
        headers=headers,
    )
    response.raise_for_status()

    return response.json()["data"]


def get_product_image(token, image_id):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(
        f"https://useast.api.elasticpath.com/v2/files/{image_id}", headers=headers
    )
    response.raise_for_status()
    return response.json()


def create_cart(token):
    carts_url = "https://useast.api.elasticpath.com/v2/carts"
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    data = {
        "data": {
            "name": "test",
        }
    }
    response = requests.post(carts_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["data"]["id"]


def add_product_to_cart(cart_id, token, product):
    cart_url = f"https://useast.api.elasticpath.com/v2/carts/{cart_id}/items/"
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    data = {
        "data": {
            "id": product,
            "type": "cart_item",
            "quantity": 1,
        }
    }
    response = requests.post(cart_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_cart(token, chat_id):
    cart_url = f"https://useast.api.elasticpath.com/v2/carts/{chat_id}/items"
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    response = requests.get(cart_url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]


def delete_product_from_cart(token, product_id, chat_id):
    url = f"https://useast.api.elasticpath.com/v2/carts/{chat_id}/items/{product_id}"
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def get_carts_sum(token, chat_id):
    carts_sum_url = f"https://useast.api.elasticpath.com/v2/carts/{chat_id}"
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    response = requests.get(carts_sum_url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["meta"]["display_price"]["with_tax"][
        "formatted"
    ]


def create_customer(token, email, chat_id):
    url = f"https://useast.api.elasticpath.com/v2/customers"
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    json_data = {
        "data": {
            "type": "customer",
            "name": str(chat_id),
            "email": email,
            "password": "",
        },
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()


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


def add_pricebook(token):
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    json_data = {
        'data': {
            'type': 'pricebook',
            'attributes': {
                'name': 'PIzzas',
                'description': 'Prices for pizza',
            },
        },
    }
    response = requests.post('https://useast.api.elasticpath.com/pcm/pricebooks', headers=headers, json=json_data)
    response.raise_for_status()
    return response.json().get('data').get('id')


def create_currency(token):
    url = 'https://useast.api.elasticpath.com/v2/currencies'
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    json_data = {
        'data': {
            'type': 'currency',
            'code': 'RUB',
            'exchange_rate': 1,
            'format': '{price} РУБ',
            'decimal_point': '.',
            'thousand_separator': ',',
            'decimal_places': 2,
            'default': True,
            'enabled': True
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()


def add_price_for_product(token, pricebook_id, product_sku, product_price):
    url = f'https://useast.api.elasticpath.com/pcm/pricebooks/{pricebook_id}/prices'
    headers = {"Authorization": "Bearer {}".format(token)}
    json_data = {
        'data': {
            'type': 'product-price',
            'attributes': {
                'currencies': {
                    'RUB': {
                        'amount': product_price * 100,
                        'includes_tax': False
                    },
                },
                'sku': product_sku
            }
        }
    }
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

        product_sku = response.json().get('data').get('attributes').get('sku')
        product_price = product['price']
        add_price_for_product(token, '7526b695-aade-4906-a2ca-7c304eb900fc', product_sku, product_price)


def add_pizzeria_address(token, slug='pizzeri-aaddresses'):
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    with open("addresses.json", "r") as my_file:
        addresses_json = my_file.read()

    addresses = json.loads(addresses_json)
    for address in addresses:
        json_data = {
            'data': {
                'type': 'entry',
                'address': address['address']['full'],
                'alias': address['alias'],
                'longitude': float(address['coordinates']['lon']),
                'latitude': float(address['coordinates']['lat'])
            }
        }
        response = requests.post(
            f'https://useast.api.elasticpath.com/v2/flows/{slug}/entries',
            headers=headers,
            json=json_data
        )
        response.raise_for_status()


def add_customer_address(token, customer_id, latitude, longitude, slug='customer-address'):
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    json_data = {
        'data': {
            'type': 'entry',
            'customer-id': str(customer_id),
            'longitude': float(longitude),
            'latitude': float(latitude)
        }
    }

    response = requests.post(
        f'https://useast.api.elasticpath.com/v2/flows/{slug}/entries',
        headers=headers,
        json=json_data
    )
    print(666, response.json())
    response.raise_for_status()


def create_flow(token, name, description):
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    json_data = {
        'data': {
            'type': 'flow',
            'name': name,
            'slug': slugify(name),
            'description': description,
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


def get_all_pizzerias(token, slug='pizzeri-aaddresses'):
    url = f'https://useast.api.elasticpath.com/v2/flows/{slug}/entries?page[limit]=100'

    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_pizzeria_by_id(token, pizzeria_id, slug='pizzeri-aaddresses'):
    url = f"https://useast.api.elasticpath.com/v2/flows/{slug}/entries/{pizzeria_id}"
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    response = requests.get(url, headers=headers)
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
