import yaml
from app import app
from poloniex import poloniex
from flask import jsonify, request

# todo: move these to a secure data store and read from that
secrets = yaml.load(open('secrets.yaml', 'r'))

api = poloniex(secrets['poloniex_key'], secrets['poloniex_secret'])

# endpoints
@app.route('/api/v1/poloniex/balances')
def returnBalances():
    nonZeroBalances = {}
    balances = api.returnBalances()
    marketdata = api.returnTicker()
    for symbol, balance in balances.items():
        if float(balance) > 0:
            nonZeroBalances[symbol] = get_balance_pair(marketdata, symbol, balance)
    return jsonify(nonZeroBalances)

def get_balance_pair(marketdata, symbol, balance):
    tmp = {}
    tmp['balance'] = balance
    if symbol == 'BTC':
        tmp['btc'] = balance
    else:
        currencypair = 'BTC_' + symbol;
        try:
            tmp['btc'] = str(get_btc_value(marketdata[currencypair]['last'], balance))
        except KeyError, e:
            print 'Data not found for currency pair: ' + currencypair
    return tmp

def get_btc_value(price, balance):
    return float(price) * float(balance)
