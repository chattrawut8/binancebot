import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

API_KEY = '6041331240427dbbf26bd671beee93f6686b57dde4bde5108672963fad02bf2e'
API_SECRET = '560764a399e23e9bc5e24d041bd3b085ee710bf08755d26ff4822bfd9393b11e'
client = Client(API_KEY, API_SECRET, testnet=True) #testnet=True

def check_position_status(symbol):
    orders = client.futures_position_information(symbol=symbol)
    if float(orders[0]['positionAmt']) > 0: return True
    else:  return False

def check_main_order_status(symbol):
    orders = client.futures_get_open_orders(symbol=symbol)
    #print('check_main_order_status', orders)
    print('total order has open is', len(orders))

    for x in orders:
        #print(x)
        if x['reduceOnly'] == False: return True
    return False

def open_position(side, symbol, high, low, order_type=ORDER_TYPE_MARKET):  
    try:
        
        pre_balance = client.futures_account_balance()
        precision = 3

        balance = int(float(pre_balance[1]['balance']))

        amount = (balance/1.05) / float(high)
        quantity = float(round(amount, precision))

        tick_price = float(low)
        low_price = float(round(tick_price, precision))

        tick_price = float(high)
        high_price = float(round(tick_price, precision))

        stoploss_percent = float(((float(high_price) - float(low_price))/float(low_price))*100)
        stoploss_percent = float(round(stoploss_percent, precision))

        print("stoploss % is ", stoploss_percent)

        if side == "BUY": tp1 = (high_price*stoploss_percent/100)+high_price
        else: tp1 = high_price - (high_price*stoploss_percent/100)
        tp1 = float(round(tp1, precision))

        if side == "BUY": tp2 = (high_price*(stoploss_percent*2)/100)+high_price
        else: tp2 = high_price - (high_price*(stoploss_percent*2)/100)
        tp2 = float(round(tp2, precision))

        if side == "BUY": tp3 = (high_price*(stoploss_percent*3)/100)+high_price
        else: tp3 = high_price - (high_price*(stoploss_percent*3)/100)
        tp3 = float(round(tp3, precision))

        quantity_tp = quantity/4
        quantity_tp = float(round(quantity_tp, precision))

        quantity_tp2 = quantity/2
        quantity_tp2 = float(round(quantity_tp2, precision))

        position_status = check_position_status(symbol)
        if position_status == True:
            print("position has ready!")
        else:
            print("position has not ready!")

        #check_main_order_status()

        print('your balance is', balance, 'USDT')
        print('your quantity', quantity)
        print('Tick price is ', high_price)

        #print(f"sending order {order_type} - {side} {quantity} {symbol}")
        if check_main_order_status(symbol) != True and check_position_status(symbol) != True:
            if side == "BUY":
                print(high_price)
                print(quantity)
                order = client.futures_create_order(symbol=symbol, side=side, type="STOP_MARKET",stopPrice=high_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)
                
                print(tp1)
                print(quantity_tp)
                order = client.futures_create_order(symbol=symbol, side="SELL", reduceOnly="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp1, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", reduceOnly="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp2, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp3, quantity=quantity_tp2, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                type="TAKE_PROFIT_MARKET",stopPrice=low_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)
            #else:
            #    order = client.futures_create_order(symbol=symbol, side=side, type="LIMIT",price=low_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)
            #    
            #    order = client.futures_create_order(symbol=symbol, side="BUY", reduceOnly="true",
            #    type="LIMIT",price=tp1, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)
#
            #    order = client.futures_create_order(symbol=symbol, side="BUY", reduceOnly="true",
            #    type="LIMIT",price=tp2, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)
#
            #    order = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
            #    type="LIMIT",price=tp3, quantity=quantity_tp2, timeInForce=TIME_IN_FORCE_GTC,)

            #    order = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
            #    type="LIMIT",price=high_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)
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
    print('')
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