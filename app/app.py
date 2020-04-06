import os
import requests
from flask import Flask


app = Flask(__name__)

@app.route("/")
def hello():
    response = fetch_from_node()
    return "hello from python<br>" + response


def fetch_from_node():
    try:
        r = requests.get(os.getenv("NODE_ENDPOINT") + '/')
    except requests.exceptions.ConnectionError:
        return 'error fetching from node'
    return r.text
