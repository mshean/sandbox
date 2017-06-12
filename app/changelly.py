import yaml, hmac, hashlib, json, requests
from app import app
from flask import jsonify, request

# todo: move these to a secure data store and read from that
secrets = yaml.load(open('secrets.yaml', 'r'))

baseurl = 'https://api.changelly.com'

# endpoints

@app.route('/api/v1/currencies')
def get_currencies():
    payload = {
      "jsonrpc": "2.0",
      "method": "getCurrencies",
      "params": {},
      "id": 1
    }
    return send_request_to_changelly(payload)

@app.route('/api/v1/min/<string:from_currency>/<string:to_currency>')
def get_min_amount(from_currency, to_currency):
    payload = {
      "jsonrpc": "2.0",
      "method": "getMinAmount",
      "params": {
        "from": from_currency,
        "to": to_currency,
      },
      "id": 1
    }
    return send_request_to_changelly(payload)

@app.route('/api/v1/exchange/<string:from_currency>/<string:to_currency>')
def get_exchange_rates(from_currency, to_currency, amount = 1):
    payload = {
      "jsonrpc": "2.0",
      "method": "getExchangeAmount",
      "params": {
        "from": from_currency,
        "to": to_currency,
        "amount": amount
      },
      "id": 1
    }
    return send_request_to_changelly(payload)

@app.route('/api/v1/exchange/<string:from_currency>/<string:to_currency>/<int:amount>')
def get_exchange_rates_specific(from_currency, to_currency, amount = 1):
    return get_exchange_rates(from_currency, to_currency, amount)

# utlity methods

def send_request_to_changelly(payload):
    headers = create_auth_headers(payload)
    r = requests.post(baseurl, json=payload, headers=headers)
    if r.status_code == 200:
      response = json.loads(r.text)
      if 'result' in response:
        return jsonify(response['result'])
      if 'error' in response:
        return jsonify(response['error'])
    return jsonify(r.text)

def create_auth_headers(payload):
    headers = {
      'api-key': secrets['key'],
      'sign': generate_signed_payload(payload)
    }
    return headers

def generate_signed_payload(payload):
    sign = hmac.new(secrets['secret'], json.dumps(payload), hashlib.sha512)
    return sign.hexdigest()
