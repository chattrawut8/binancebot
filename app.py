import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *
from math import ceil, floor
from binance.exceptions import BinanceAPIException

app = Flask(__name__)

API_KEY = 'E2TnptYKp2MigaCSWuMPuHBtJqIwwJnMqghYouRAUNh08zVZLGwoucb4N0kuDFK2'
API_SECRET = 'JmNksYt81bikkoMY6R4sqVlSSjsK0AxIrS8dw0IxCmPzWE2BwZ9l3tm3vUA2Gry8'
client = Client(API_KEY, API_SECRET) #testnet=True

def cancel_all_order(symbol):
    #client.futures_cancel_all_open_orders(symbol=symbol)
    client = Client(API_KEY, API_SECRET)
    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)
    
    print('Old json orders',json_object)

    with open('orders.json', 'w') as outfile:
        json.dump('', outfile)
    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)
    
    print('New json orders',json_object)

    for x in json_object:
        try:
            client.futures_cancel_order(symbol=symbol, orderId=x['orderId'])
        except BinanceAPIException as e:
            print('\nClose old order\ncan not find ',x['orderId'])
            client = Client(API_KEY, API_SECRET)
            continue

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
    orders = sorted(orders, key=lambda x: x['stopPrice'])

    with open('orders.json', 'w') as outfile:
        json.dump(orders, outfile)
    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)
    print('\n' , 'total order ' , len(json_object))
    for x in json_object:
        print('order ID ' , x['orderId'] , ' | ', ' side ' , x['side'] , ' price ' , x['stopPrice'] , ' | ' , ' reduceOnly ' , x['reduceOnly'] )

    index = [x['reduceOnly'] for x in json_object].index(False)
    print('Main Order Index = ' , index) 

    print('MAIN ORDER \n',client.futures_get_order(symbol=symbol, orderId=json_object[index]['orderId']))

def check_hit_stoploss(symbol):
    client = Client(API_KEY, API_SECRET)
    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)

    print("pass1")
    index = [x['reduceOnly'] for x in json_object].index(False)
    print("pass2 ",index)
    if json_object[index]['side'] == 'BUY':
        try:
            print("pass3")
            client.futures_cancel_order(symbol=symbol, orderId=json_object[0]['orderId'])
            print("pass4")
        except BinanceAPIException as e:
            print("pass5")
            print('\n Has hit stoploss BUY order!')
            client = Client(API_KEY, API_SECRET)
            cancel_all_order(symbol)
            print("pass6")
    else:
        len_orders = int(len(json_object)) - 1
        try:
            client.futures_cancel_order(symbol=symbol, orderId=json_object[len_orders]['orderId'])
        except BinanceAPIException as e:
            print('\n Has hit stoploss SELL order!')
            client = Client(API_KEY, API_SECRET)
            cancel_all_order(symbol)

def check_close_order(symbol): #เมื่อมีการชนเขต SLO หรือไม่เข้าออเดอร์ภายใน 5 แท่ง
    try:
        print('!!!check_hit_stoploss!!!')
        check_hit_stoploss(symbol=symbol)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

"""def change_stoploss():
    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)
    len_order = len(json_object)

    if len_order == 5: #risk/reward 1/3
        if check_hit_tp2() == True: 
            change_stoploss_to_1reward()
        elif check_hit_tp1() == True: #เป้าแรก ทำกำไร25% ที่ 1/3
            change_stoploss_to_0risk()
    elif len_order == 4: #risk/reward 1/2
        if check_hit_tp1() == True: #เป้าแรก ทำกำไร25% ที่ 1/2
            change_stoploss_to_0risk()
    elif len_order == 3: #risk/reward 1/1
        if check_hit_tp1() == True: #เป้าแรก ทำกำไร25% ที่ 0.5/1
            change_stoploss_to_0risk()
"""

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
                order = client.futures_create_order(symbol=symbol, side=side,
                type="STOP_MARKET",stopPrice=high_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)

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
                order = client.futures_create_order(symbol=symbol, side=side,
                type="STOP_MARKET",stopPrice=low_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)
                
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

@app.route('/check', methods=['POST'])
def check():
    print(request.data)
    print('')
    data = json.loads(request.data)
    
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }

    symbol = data['ticker']
    check_response = check_close_order(symbol)

    if check_response:
        return {
            "code": "success",
            "message": "check executed"
        }
    else:
        print("order failed")

        return {
            "code": "error",
            "message": "check failed"
        }