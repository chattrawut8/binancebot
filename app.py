import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from math import ceil, floor

app = Flask(__name__)

API_KEY = '6041331240427dbbf26bd671beee93f6686b57dde4bde5108672963fad02bf2e'
API_SECRET = '560764a399e23e9bc5e24d041bd3b085ee710bf08755d26ff4822bfd9393b11e'
client = Client(API_KEY, API_SECRET, testnet=True) #testnet=True

def cancel_all_order(symbol):
    client.futures_cancel_all_open_orders(symbol=symbol)

def check_position_status(symbol):
    orders = client.futures_position_information(symbol=symbol)
    if float(orders[0]['positionAmt']) > 0: return True
    else:  return False

def check_main_order_type(symbol):
    orders = client.futures_get_open_orders(symbol=symbol)
    for x in orders:
        if x['reduceOnly'] == False:
            return str(x['side'])
    return 0

def check_main_order_status(symbol):
    orders = client.futures_get_open_orders(symbol=symbol)
    #print('total order has open is', len(orders))
    for x in orders:
        if x['reduceOnly'] == False:
            return True
    return False

def save_orders_json(symbol):
    orders = client.futures_get_open_orders(symbol=symbol)
    with open('orders.json', 'w') as outfile:
        json.dump(orders, outfile)
    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)
    print('\n' , 'total order ' , len(json_object))
    for x in json_object:
        print('order ID ' , x['orderId'] , ' | ', ' side ' , x['side'] , ' price ' , x['stopPrice'] , ' | ' , ' reduceOnly ' , x['reduceOnly'] )

def open_position(side, symbol, high, low, order_type=ORDER_TYPE_MARKET):  
    try:
        pre_balance = client.futures_account_balance()
        precision = 2

        balance = int(float(pre_balance[1]['balance']))

        amount = (balance/1.025) / float(high)
        quantity = float(round(amount, precision))

        tick_price = float(low)
        low_price = float(floor(tick_price))

        tick_price = float(high)
        high_price = float(ceil(tick_price))

        stoploss_percent = float(((float(high_price) - float(low_price))/float(low_price))*100)
        stoploss_percent = float(round(stoploss_percent, precision))

        print("stoploss % is ", stoploss_percent)

        if side == "BUY": tp1 = (high_price*stoploss_percent/100)+high_price
        else: tp1 = low_price - (low_price*stoploss_percent/100)
        tp1 = float(round(tp1, precision))
        print('Take Profit 1 = ',tp1)

        if side == "BUY": tp2 = (high_price*(stoploss_percent*2)/100)+high_price
        else: tp2 = low_price - (low_price*(stoploss_percent*2)/100)
        tp2 = float(round(tp2, precision))
        print('Take Profit 2 = ',tp2)

        if side == "BUY": tp3 = (high_price*(stoploss_percent*3)/100)+high_price
        else: tp3 = low_price - (low_price*(stoploss_percent*3)/100)
        tp3 = float(round(tp3, precision))
        print('Take Profit 3 = ',tp3)

        quantity_tp = quantity/4
        quantity_tp = float(round(quantity_tp, precision))

        quantity_tp2 = quantity/2
        quantity_tp2 = float(round(quantity_tp2, precision))

        position_status = check_position_status(symbol)
        if position_status == True:
            print("position has ready!")
        else:
            print("position has not ready!")

        print('your balance is', balance, 'USDT')
        print('your quantity', quantity)
        print('Tick price is ', high_price)

        #print(f"sending order {order_type} - {side} {quantity} {symbol}")
        
        if check_main_order_status(symbol) == True and check_position_status(symbol) == False:
            mainOrder_side = check_main_order_type(symbol)
            if mainOrder_side != side:
                cancel_all_order(symbol)
                print("New opposite signal so cancel all order")

        if check_main_order_status(symbol) == False and check_position_status(symbol) == False:
            if side == "BUY":
                order = client.futures_create_order(symbol=symbol, side=side, type="STOP_MARKET",stopPrice=high_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)
                
                order = client.futures_create_order(symbol=symbol, side="SELL", reduceOnly="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp1, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", reduceOnly="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp2, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp3, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                type="STOP_MARKET",stopPrice=low_price, timeInForce=TIME_IN_FORCE_GTC,)

                save_orders_json(symbol)

            elif side == "SELL":
                order = client.futures_create_order(symbol=symbol, side=side, type="STOP_MARKET",stopPrice=low_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)
                
                order = client.futures_create_order(symbol=symbol, side="BUY", reduceOnly="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp1, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="BUY", reduceOnly="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp2, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp3, quantity=quantity_tp2, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
                type="STOP_MARKET",stopPrice=high_price, timeInForce=TIME_IN_FORCE_GTC,)

                save_orders_json(symbol)
        else:
            print('--- Order/Position has ready can not open new order!!! ---')
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