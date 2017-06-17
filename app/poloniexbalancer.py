import yaml
import time
from app import app
from poloniex import poloniex
from flask import jsonify

# todo: move these to a secure data store and read from that
secrets = yaml.load(open('secrets.yaml', 'r'))

api = poloniex(secrets['poloniex_key'], secrets['poloniex_secret'])

min_transaction_amount = 0.005

# endpoints
@app.route('/api/v1/poloniex/balances')
def returnBalances():
    return jsonify(get_balances(api.returnTicker()))

@app.route('/api/v1/poloniex/dryrun')
def deversify_dry():
    return jsonify(diversify())

@app.route('/api/v1/poloniex/diversify')
def diversify_execute():
    meta = diversify()
    sell = meta['trades']['sell']
    results = {'buy': {}, 'sell': {}}
    for ticker, asset_meta in sell.items():
        pair = 'BTC_' + ticker
        print 'selling %s %s at rate %s' % (asset_meta['amount'], ticker, asset_meta['rate'])
        results['sell'][ticker] = api.sell(currencyPair=pair, rate=asset_meta['rate'], amount=asset_meta['amount'])
        print 'sold'
        time.sleep(.2)
    buy = meta['trades']['buy']
    for ticker, asset_meta in buy.items():
        pair = 'BTC_' + ticker
        print 'buying %s %s at rate %s' % (asset_meta['amount'], ticker, asset_meta['rate'])
        results['buy'][ticker] = api.buy(currencyPair=pair, rate=asset_meta['rate'], amount=asset_meta['amount'])
        print 'bought'
        time.sleep(.2)
    return jsonify(results)

def diversify():
    marketdata = api.returnTicker()
    balances = get_balances(marketdata)
    btc_sum = 0
    for symbol, balance in balances.items():
        btc_sum += float(balance['btc'])
    target_allocation = btc_sum / len(balances)
    result = {
        'balances': balances,
        'min_btc_transaction_amount': str(min_transaction_amount),
        'target_allocation': format(target_allocation, '.8f'),
        'trades': get_trades(marketdata, balances, target_allocation)
    }
    return result

def get_trades(marketdata, balances, target_allocation):
    trades = {'buy': {}, 'sell': {}}
    for symbol, balance in balances.items():
        diff = target_allocation - float(balance['btc'])
        if abs(diff) > min_transaction_amount and symbol != 'BTC':
            if diff > 0:
                rate = get_price(marketdata, symbol, 'lowestAsk')
                trades['buy'][symbol] = {
                    'rate': rate,
                    'amount': format(abs(diff) / float(rate), '.8f')
                }
            else:
                rate = get_price(marketdata, symbol, 'highestBid')
                trades['buy'][symbol] = {
                    'rate': rate,
                    'amount': format(abs(diff) / float(rate), '.8f')
                }
    return trades

def get_balances(marketdata):
    nonZeroBalances = {}
    balances = api.returnBalances()
    for symbol, balance in balances.items():
        if float(balance) > 0:
            nonZeroBalances[symbol] = get_balance_pair(marketdata, symbol, balance)
    return nonZeroBalances

def get_balance_pair(marketdata, symbol, balance):
    price = get_price(marketdata, symbol, 'last')
    return {
        'balance': balance,
        'btc': format(float(price) * float(balance), '.8f')
    }

def get_price(marketdata, symbol, price_type):
    if symbol == 'BTC':
        return 1
    else:
        currencypair = 'BTC_' + symbol;
        try:
            return marketdata[currencypair][price_type]
        except KeyError, e:
            print 'Price type ' + price_type + ' data not found for currency pair: ' + currencypair
