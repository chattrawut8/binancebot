import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

API_KEY = '6041331240427dbbf26bd671beee93f6686b57dde4bde5108672963fad02bf2e'
API_SECRET = '560764a399e23e9bc5e24d041bd3b085ee710bf08755d26ff4822bfd9393b11e'
client = Client(API_KEY, API_SECRET,testnet=True)

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        respontext = client.futures_account_balance()
        candles = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_4HOUR)

        price = client.get_symbol_ticker(symbol="BTCUSDT")

        buy_quantity = round(100 / float(price['price']))

        print(candles[0][1])
        print(respontext[1]['balance'])
        print(f"sending order {order_type} - {side} {quantity} {symbol}")
        
        #order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        order = client.futures_create_order(symbol="BTCUSDT", side="BUY", type="LIMIT", price=price['price'], quantity=buy_quantity, timeInForce=TIME_IN_FORCE_GTC,)
        
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return order

@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    print(request.data)
    data = json.loads(request.data)
    
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }

    side = data['strategy']['order_action'].upper()
    quantity = data['strategy']['order_contracts']
    order_response = order(side, quantity, "DOGEUSDT")

    if order_response:
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")

        return {
            "code": "error",
            "message": "order failed"
        }