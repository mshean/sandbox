import yaml
from app import app
from poloniex import poloniex
from flask import jsonify, request

# todo: move these to a secure data store and read from that
secrets = yaml.load(open('secrets.yaml', 'r'))

api = poloniex(secrets['poloniex_key'], secrets['poloniex_secret'])

min_transaction_amount = 0.005

# endpoints
@app.route('/api/v1/poloniex/balances')
def returnBalances():
    return jsonify(get_balances(api.returnTicker()))

@app.route('/api/v1/poloniex/diversifydry')
def deversify_dry():
    return jsonify(diversify())

@app.route('/api/v1/poloniex/diversify')
def diversify_execute():
    meta = diversify()
    sell = meta['trades']['sell']
    for ticker, asset_meta in sell.items():
        pair = 'BTC_' + ticker
        print 'selling %s %s at rate %s' % (asset_meta['amount'], ticker, asset_meta['price'])
        api.sell(pair, asset_meta['amount'], asset_meta['price'])
        print 'sold'
        time.sleep(10)
    buy = meta['trades']['buy']
    for ticker, asset_meta in buy.items():
        pair = 'BTC_' + ticker
        print 'buying %s %s at rate %s' % (asset_meta['amount'], ticker, asset_meta['price'])
        api.buy(pair, asset_meta['price'], asset_meta['amount'])
        print 'bought'
        time.sleep(10)
    return returnBalances()

def diversify():
    marketdata = api.returnTicker()
    balances = get_balances(marketdata)
    btc_sum = 0
    for symbol, balance in balances.items():
        btc_sum += float(balance['btc'])
    target_allocation = btc_sum / len(balances)
    result = {}
    result['balances'] = balances
    result['target_allocation'] = format(target_allocation, '.8f')
    result['trades'] = get_trades(marketdata, balances, target_allocation)
    return result

def get_trades(marketdata, balances, target_allocation):
    buy = {}
    sell = {}
    trades = {}
    for symbol, balance in balances.items():
        diff = target_allocation - float(balance['btc'])
        if abs(diff) > min_transaction_amount and symbol != 'BTC':
            tmp = {}
            tmp['amount'] = format(abs(diff), '.8f')
            if diff > 0:
                tmp['price'] = get_price(marketdata, symbol, 'lowestAsk')
                buy[symbol] = tmp
            else:
                tmp['price'] = get_price(marketdata, symbol, 'highestBid')
                sell[symbol] = tmp
    trades['buy'] = buy
    trades['sell'] = sell
    return trades

def get_balances(marketdata):
    nonZeroBalances = {}
    balances = api.returnBalances()
    for symbol, balance in balances.items():
        if float(balance) > 0:
            nonZeroBalances[symbol] = get_balance_pair(marketdata, symbol, balance)
    return nonZeroBalances

def get_balance_pair(marketdata, symbol, balance):
    tmp = {}
    tmp['balance'] = balance
    price = get_price(marketdata, symbol, 'last')
    tmp['btc'] = format(float(price) * float(balance), '.8f')
    return tmp

def get_price(marketdata, symbol, price_type):
    if symbol == 'BTC':
        return 1
    else:
        currencypair = 'BTC_' + symbol;
        try:
            return marketdata[currencypair][price_type]
        except KeyError, e:
            print 'Price type ' + price_type + ' data not found for currency pair: ' + currencypair
