import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

API_KEY = 'RtMIY2hRqqBBi1Fqm7GbarnI96UJKrxgF9oBoXiQLZNUsHSMTkua24OCVIp8wGva'
API_SECRET = 'VGttXSwMzib26jz97UMOLCqdUJ2Ynn8erYQKtolnK8LFZQdZOGSCK6B5FDI75MVd'
client = Client(API_KEY, API_SECRET,testnet=True)

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print(f"sending order {order_type} - {side} {quantity} {symbol}")
        #order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        order = client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
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
    order_response = order(side, quantity, "DOGEUSD")

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