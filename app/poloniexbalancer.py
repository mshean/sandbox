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
        print 'selling ' + asset_meta['amount'] + ' ' + ticker + ' at rate ' + asset_meta['price']
        api.sell('BTC_' + ticker, float(asset_meta['price']), float(asset_meta['amount']))
        print 'sold'
        time.sleep(10)
    buy = meta['trades']['buy']
    for ticker, asset_meta in buy.items():
        print 'buying ' + asset_meta['amount'] + ' ' + ticker + ' at rate ' + asset_meta['price']
        api.buy('BTC_' + ticker, float(asset_meta['price']), float(asset_meta['amount']))
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
    result['target_allocation'] = str(target_allocation)
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
            tmp['amount'] = str(abs(diff))
            if diff > 0:
                tmp['price'] = str(get_price(marketdata, symbol, abs(diff), 'lowestAsk'))
                buy[symbol] = tmp
            else:
                tmp['price'] = str(get_price(marketdata, symbol, abs(diff), 'highestBid'))
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
    tmp['btc'] = get_price(marketdata, symbol, balance, 'last')
    return tmp

def get_price(marketdata, symbol, balance, price_type):
    if symbol == 'BTC':
        return balance
    else:
        currencypair = 'BTC_' + symbol;
        try:
            return str(get_btc_value(marketdata[currencypair][price_type], balance))
        except KeyError, e:
            print 'Price type ' + price_type + ' data not found for currency pair: ' + currencypair

def get_btc_value(price, balance):
    return float(price) * float(balance)
