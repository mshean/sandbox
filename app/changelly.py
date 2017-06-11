import yaml, hmac
from app import app
from flask import jsonify, request

# todo: move these to a secure data store and read from that
secrets = yaml.load(open('secrets.yaml', 'r'))

baseurl = 'https://api.changelly.com'

@app.route('/api/v1/secrets')
def get_secrets():
    return jsonify({'key': secrets['key'], 'secret': secrets['secret']})
