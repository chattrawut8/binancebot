import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

API_KEY = '6041331240427dbbf26bd671beee93f6686b57dde4bde5108672963fad02bf2e'
API_SECRET = '560764a399e23e9bc5e24d041bd3b085ee710bf08755d26ff4822bfd9393b11e'
client = Client(API_KEY, API_SECRET, testnet=True) #testnet=True

def check_position_status():
    orders = client.futures_position_information(symbol="BTCUSDT")
    if float(orders[0]['positionAmt']) > 0: return True
    else:  return False

def check_main_order_status():
    orders = client.futures_get_open_orders(symbol="BTCUSDT")
    #print('check_main_order_status', orders)
    print('total order has open is', len(orders))

    for x in orders:
        print(x)
        if x['reduceOnly'] == False: return True
    return False

def open_position(side, symbol, high, low, order_type=ORDER_TYPE_MARKET):  
    try:
        pre_balance = client.futures_account_balance()
        precision = 3

        balance = int(pre_balance[1]['balance'])

        print(balance)

        amount = (balance/1.05) / float(high)
        quantity = "{:0.0{}f}".format(amount, precision)

        tick_price = float(high)
        price = "{:0.0{}f}".format(tick_price, precision)

        position_status = check_position_status()
        if position_status == True:
            print("position has ready!")
        else:
            print("position has not ready!")

        #check_main_order_status()

        print('your balance is', balance[1]['balance'], 'USDT')
        print('your quantity', quantity)
        print('Tick price is ', price)

        #print(f"sending order {order_type} - {side} {quantity} {symbol}")

        if check_main_order_status() != True:
            order = client.futures_create_order(symbol=symbol, side=side, type="STOP_LOSS", price=price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)
        else:
            print('--- Order has ready can not open new order!!! ---')
            return False

    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return order
 
@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    #print(request.data)
    print('\n')
    data = json.loads(request.data)
    
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }
    high = data['bar']['high']
    low = data['bar']['low']
    symbol = data['ticker']
    side = data['strategy']['order_action'].upper()
    order_response = open_position(side, symbol, high, low)

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


def close_position():return 0 #เมื่อมีการชนเขต SLO หรือไม่เข้าออเดอร์ภายใน 5 แท่ง

def open_stoploss():return 0
def open_takeprofit():return 0

def change_stoploss():return 0
def change_takeprofit():return 0

def close_order(): return 0 #สำหรับปิดออเดอร์ TP/SL เมือ position มีการเปลียนแปลง

def every_1minute(): return 0 #เช็คสถานะราคาทุกๆนาที

def fast_close_position(): return 0