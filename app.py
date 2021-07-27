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

print("Start Bot")
client.futures_cancel_all_open_orders(symbol='ETHUSDT')

with open('orders.json', 'w') as outfile:
    json.dump('', outfile)
with open('orders_status.json', 'w') as outfile:
    json.dump('', outfile)
with open('tptype.json', 'w') as outfile:
    json.dump('', outfile)

def cancel_all_order(symbol):
    #client.futures_cancel_all_open_orders(symbol=symbol)
    client = Client(API_KEY, API_SECRET)
    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)

    for x in json_object:
        try:
            client.futures_cancel_order(symbol=symbol, orderId=x['orderId'])
        except BinanceAPIException as e:
            client = Client(API_KEY, API_SECRET)
            continue
    
    with open('orders.json', 'w') as outfile:
        json.dump('', outfile)

def check_position_status(symbol):
    orders = client.futures_position_information(symbol=symbol)
    if float(orders[0]['positionAmt']) > 0:
        return True
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
    orders.sort(key=lambda x: x['stopPrice'])

    with open('orders.json', 'w') as outfile:
        json.dump(orders, outfile)
    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)
    print('\n' , 'total order ' , len(json_object))
    for x in json_object:
        print('order ID ' , x['orderId'] , ' | ', ' side ' , x['side'] , ' price ' , x['stopPrice'] , ' | ' , ' reduceOnly ' , x['reduceOnly'] )

def save_orders_status_1to3_json():

    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)

    index = [x['reduceOnly'] for x in json_object].index(False)

    dictionary ={
        "tp1":{"price":json_object[index+1]['stopPrice'],"orderId":json_object[index+1]['orderId']},
        "tp2":{"price":json_object[index+2]['stopPrice'],"orderId":json_object[index+2]['orderId']}}

    with open("orders_status.json", "w") as outfile:
        json.dump(dictionary, outfile)
    
    with open('orders_status.json', 'r') as openfile:
        json_object_status = json.load(openfile)
        
    print('\njson status')
    print(json_object_status)


def save_orders_status_other_json():

    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)

    index = [x['reduceOnly'] for x in json_object].index(False)

    dictionary ={"tp1":{"price":json_object[index+1]['stopPrice'],"orderId":json_object[index+1]['orderId']}}

    with open("orders_status.json", "w") as outfile:
        json.dump(dictionary, outfile)

    with open('orders_status.json', 'r') as openfile:
        json_object_status = json.load(openfile)
        
    print('\njson status')
    print(json_object_status)
        
def check_hit_SL_TP(symbol):
    client = Client(API_KEY, API_SECRET)
    
    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)

    orders = client.futures_get_open_orders(symbol=symbol)

    try:
        index = [x['reduceOnly'] for x in orders].index(False)
    except Exception as e:
        print('can not find main orders')
        client = Client(API_KEY, API_SECRET)
        if check_position_status(symbol=symbol) == True:
            print('but have position')
        else:
            cancel_all_order(symbol)
            return True

    try:
        index = [x['reduceOnly'] for x in json_object].index(False)
        if json_object[index]['side'] == 'BUY':
            check_sl_order = [x['orderId'] for x in orders].index(json_object[index-1]['orderId'])

        else:
            len_orders = int(len(json_object)) - 1
            check_sl_order = [x['orderId'] for x in orders].index(json_object[index+1]['orderId'])

    except Exception as e:
        print('\n Has hit ST order!')
        client = Client(API_KEY, API_SECRET)
        cancel_all_order(symbol)
        return True

    return False

def check_close_order(symbol): #เมื่อมีการชนเขต SLO หรือไม่เข้าออเดอร์ภายใน 5 แท่ง
    print('!!!check hit SL or all TP!!!')
    return check_hit_SL_TP(symbol=symbol)

def check_hit_TP(symbol,index):

    with open('orders_status.json', 'r') as openfile:
        json_object = json.load(openfile)

    orders = client.futures_get_open_orders(symbol=symbol)

    try:
        print('check stoploss order id ', json_object[index]['orderId'])
        check_sl_order = [x['orderId'] for x in orders].index(json_object[index]['orderId'])
        print('is ',check_sl_order,'\n')
    except Exception as e:
        return True
    
    return False

def change_new_stoploss(symbol,index):
    print('Have change new stoploss!!')
    with open('orders_status.json', 'r') as openfile:
        json_object_status = json.load(openfile)

    with open('orders.json', 'r') as openfile:
        json_object = json.load(openfile)

    orders = client.futures_get_open_orders(symbol=symbol)

    try:
        client.futures_cancel_order(symbol=symbol, orderId=json_object_status[0]['orderId'])
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    try:
        index = [x['reduceOnly'] for x in json_object].index(False)
        if json_object[index]['side'] == 'BUY':
            order = client.futures_create_order(orderId=json_object_status[index]['orderId'],symbol=symbol, side="SELL", closePosition="true",
            type="STOP_MARKET",stopPrice=json_object_status[index]['price'], timeInForce=TIME_IN_FORCE_GTC,)
        elif json_object[index]['side'] == 'SELL':
            order = client.futures_create_order(orderId=json_object_status[index]['orderId'],symbol=symbol, side="BUY", closePosition="true",
            type="STOP_MARKET",stopPrice=json_object_status[index]['price'], timeInForce=TIME_IN_FORCE_GTC,)
        print('new stoploss price = ', json_object_status[index]['price'],)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

def change_stoploss(symbol):
    with open('tptype.json', 'r') as openfile:
        json_object = json.load(openfile)
    type_tp = json_object['type']

    if type_tp == '1to3': #risk/reward 1/3
        if check_hit_TP(symbol,1) == True: 
            change_new_stoploss(symbol,1)
        elif check_hit_TP(symbol,0) == True: #เป้าแรก ทำกำไร25% ที่ 1/3
            change_new_stoploss(symbol,0)
        else:
            print('dont have any change SL')
    elif type_tp == '1to2': #risk/reward 1/2
        if check_hit_TP(symbol,0) == True: #เป้าแรก ทำกำไร25% ที่ 1/2
            change_new_stoploss(symbol,0)
        else:
            print('dont have any change SL')
    elif type_tp == '1to1': #risk/reward 1/1
        if check_hit_TP(symbol,0) == True: #เป้าแรก ทำกำไร25% ที่ 0.5/1
            change_new_stoploss(symbol,0)
        else:
            print('dont have any change SL')
    else:
        print('error')

def save_TP_type(tp_type):
    dictionary ={"type":tp_type}
    with open("tptype.json", "w") as outfile:
        json.dump(dictionary, outfile)

def open_position(side, symbol, high, low, order_type=ORDER_TYPE_MARKET): 
    try:
        pre_balance = client.futures_account_balance()
        precision = 3

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
        
        quantity_tp = quantity/4
        quantity_tp = float(round(quantity_tp, precision))
        
        if stoploss_percent >= 15:
            type_tp = '1to1'
        elif stoploss_percent >= 6:
            type_tp = '1to2'
        else:
            type_tp = '1to3'
        print('type take profit = ',type_tp)

        save_TP_type(type_tp)

        if type_tp == '1to3':
            if side == "BUY": tp1 = (high_price*stoploss_percent/100)+high_price
            else: tp1 = low_price - (low_price*stoploss_percent/100)
            tp1 = float(round(tp1, precision))
            print('Take Profit 1 = ',tp1)

            if side == "BUY": tp2 = (high_price*(stoploss_percent*2)/100)+high_price
            else: tp2 = low_price - (low_price*(stoploss_percent*2)/100)
            tp2 = float(round(tp2, precision))
            print('Take Profit 2 = ',tp2)

            if side == "BUY": final_tp = (high_price*(stoploss_percent*3)/100)+high_price
            else: final_tp = low_price - (low_price*(stoploss_percent*3)/100)
            final_tp = float(round(final_tp, precision))
            print('Take Profit 3 = ',final_tp)

        if type_tp == '1to2':
            if side == "BUY": tp1 = (high_price*stoploss_percent/100)+high_price
            else: tp1 = low_price - (low_price*stoploss_percent/100)
            tp1 = float(round(tp1, precision))
            print('Take Profit 1 = ',tp1)

            if side == "BUY": final_tp = (high_price*(stoploss_percent*2)/100)+high_price
            else: final_tp = low_price - (low_price*(stoploss_percent*2)/100)
            final_tp = float(round(final_tp, precision))
            print('Take Profit 2 = ',final_tp)

        if type_tp == '1to1':
            if side == "BUY": tp1 = (high_price*(stoploss_percent/2)/100)+high_price
            else: tp1 = low_price - (low_price*(stoploss_percent/2)/100)
            tp1 = float(round(tp1, precision))
            print('Take Profit 1 = ',tp1)

            if side == "BUY": final_tp = (high_price*stoploss_percent/100)+high_price
            else: final_tp = low_price - (low_price*stoploss_percent/100)
            final_tp = float(round(final_tp, precision))
            print('Take Profit 2 = ',final_tp)

        position_status = check_position_status(symbol)
        if position_status == True:
            print("position has ready!")
        else:
            print("position has not ready!")

        print('your balance is', balance, 'USDT')
        print('your quantity', quantity)
        print('Tick price is ', high_price)
        
        if check_main_order_status(symbol) == True and check_position_status(symbol) == False:
            mainOrder_side = check_main_order_type(symbol)
            if mainOrder_side != side:
                cancel_all_order(symbol)
                print("New opposite signal so cancel all order")

        if check_main_order_status(symbol) == False and check_position_status(symbol) == False:
            cancel_all_order(symbol)
            if side == "BUY":
                order = client.futures_create_order(symbol=symbol, side=side,
                type="STOP_MARKET",stopPrice=high_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", reduceOnly="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp1, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                if type_tp == '1to3':
                    order = client.futures_create_order(symbol=symbol, side="SELL", reduceOnly="true",
                    type="TAKE_PROFIT_MARKET",stopPrice=tp2, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                type="TAKE_PROFIT_MARKET",stopPrice=final_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                type="STOP_MARKET",stopPrice=low_price, timeInForce=TIME_IN_FORCE_GTC,)

                save_orders_json(symbol)

                if type_tp == '1to3':
                    save_orders_status_1to3_json()
                else:
                    save_orders_status_other_json()

            elif side == "SELL":
                order = client.futures_create_order(symbol=symbol, side=side,
                type="STOP_MARKET",stopPrice=low_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)
                
                order = client.futures_create_order(symbol=symbol, side="BUY", reduceOnly="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp1, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                if type_tp == '1to3':
                    order = client.futures_create_order(symbol=symbol, side="BUY", reduceOnly="true",
                    type="TAKE_PROFIT_MARKET",stopPrice=tp2, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
                type="TAKE_PROFIT_MARKET",stopPrice=final_tp, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
                type="STOP_MARKET",stopPrice=high_price, timeInForce=TIME_IN_FORCE_GTC,)

                save_orders_json(symbol)

                if type_tp == '1to3':
                    save_orders_status_1to3_json()
                else:
                    save_orders_status_other_json()
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
    #print(request.data)
    print('')
    data = json.loads(request.data)
    
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }

    symbol = data['ticker']
    #check_close_order(symbol)
    if check_close_order(symbol) == False:
        print('chack change stoloss')
        change_stoploss(symbol)
    return {
            "code": "success",
            "message": "check executed"
        }