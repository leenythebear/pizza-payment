import json
import os

import redis
from dotenv import load_dotenv

import requests

with open("addresses.json", "r") as my_file:
    addresses_json = my_file.read()

addresses = json.loads(addresses_json)
# print(addresses)

_database = None

load_dotenv()
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

db_host = os.environ["DATABASE_HOST"]
db_port = os.environ["DATABASE_PORT"]
db_password = os.environ["DATABASE_PASSWORD"]


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


if __name__ == "__main__":
    db = get_database_connection(db_host, db_port, db_password)
    token = get_token(client_id, client_secret, db)
    response = add_products(token)
