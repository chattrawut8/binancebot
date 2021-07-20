import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

API_KEY = '6041331240427dbbf26bd671beee93f6686b57dde4bde5108672963fad02bf2e'
API_SECRET = '560764a399e23e9bc5e24d041bd3b085ee710bf08755d26ff4822bfd9393b11e'
client = Client(API_KEY, API_SECRET,testnet=True)

def check_position_status():
    orders = client.futures_position_information(symbol="BTCUSDT")
    if float(orders['positionAmt']) > 0: return True
    else:  return False

def open_position(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):  
    try:
        respontext = client.futures_account_balance()
        #candles = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_4HOUR)
        coin_price = client.get_symbol_ticker(symbol="BTCUSDT")

        amount = 100 / float(coin_price['price'])
        precision = 3
        buy_quantity = "{:0.0{}f}".format(amount, precision)

        amount2 = float(coin_price['price'])
        total_price = "{:0.0{}f}".format(amount2, precision)

        position_status = check_position_status()
        if position_status == True:
            print("position has ready!")
        else:
            print("position has not ready!")

        print('your USDT', respontext[1]['balance'])
        print(symbol,' price is ',total_price)
        print('your quantity', buy_quantity)
        print(f"sending order {order_type} - {side} {quantity} {symbol}")

        order = client.futures_create_order(orderId="mainOrder",symbol="BTCUSDT", side="BUY", type="LIMIT", price=total_price, quantity=buy_quantity, timeInForce=TIME_IN_FORCE_GTC,)

    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return order
def close_position():return 0 #เมื่อมีการชนเขต SLO หรือไม่เข้าออเดอร์ภายใน 5 แท่ง

def open_stoploss():return 0
def open_takeprofit():return 0

def change_stoploss():return 0
def change_takeprofit():return 0

def close_order(): return 0 #สำหรับปิดออเดอร์ TP/SL เมือ position มีการเปลียนแปลง

def every_1minute(): return 0 #เช็คสถานะราคาทุกๆนาที

def fast_close_position(): return 0
 
@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    #print(request.data)
    data = json.loads(request.data)
    
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }

    side = data['strategy']['order_action'].upper()
    quantity = data['strategy']['order_contracts']
    order_response = open_position(side, quantity, "DOGEUSDT")

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

@app.route('/orders')
def orders():
    orders = client.futures_get_open_orders(symbol="BTCUSDT")
    print(orders)