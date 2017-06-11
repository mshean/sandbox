import yaml, hmac, hashlib, json, requests
from app import app
from flask import jsonify, request

# todo: move these to a secure data store and read from that
secrets = yaml.load(open('secrets.yaml', 'r'))

baseurl = 'https://api.changelly.com'

@app.route('/api/v1/secrets')
def get_secrets():
    return jsonify({'key': secrets['key'], 'secret': secrets['secret']})

@app.route('/api/v1/currencies')
def get_currencies():
    payload = {
      "jsonrpc": "2.0",
      "method": "getCurrencies",
      "params": {},
      "id": 1
    }
    headers = generate_signed_headers(payload)
    r = requests.post(baseurl, json=payload, headers=headers)
    if r.status_code == 200:
      response = json.loads(r.text)
      return jsonify(response['result'])
    else:
      return jsonify(r.text)

def generate_signed_headers(payload):
    sign = hmac.new(secrets['secret'], json.dumps(payload), hashlib.sha512);
    headers = {
      'api-key': secrets['key'],
      'sign': sign.hexdigest()
    }
    return headers
