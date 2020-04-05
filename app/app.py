import os
import requests
from flask import Flask


app = Flask(__name__)

@app.route("/")
def hello():
    response = fetch_from_node()
    return "hello from python\n" + response


def fetch_from_node():
    try:
        r = requests.get('http://'
                         + os.getenv("REQUEST_HOST")
                         + ':'
                         + os.getenv("REQUEST_PORT")
                         + '/')
    except requests.exceptions.ConnectionError:
        return 'error fetching from node'
    return r.text
