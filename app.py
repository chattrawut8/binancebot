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

config.all_orders = []
config.orders_status = []
config.neworder = []
config.type_tp = ''
config.current_tp = 0

def clear_current_tp():
    config.current_tp = 0

def cancel_all_order(symbol):
    #client.futures_cancel_all_open_orders(symbol=symbol)
    client = Client(API_KEY, API_SECRET)

    for x in config.all_orders:
        try:
            client.futures_cancel_order(symbol=symbol, orderId=x['orderId'])
        except BinanceAPIException as e:
            client = Client(API_KEY, API_SECRET)
            continue
    
    config.all_orders = []

def check_position_status(symbol):
    orders = client.futures_position_information(symbol=symbol)
    print('current posotion quantity = ',orders[0]['positionAmt'])
    if float(orders[0]['positionAmt']) != 0:
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
    orders.sort(key=lambda x: float(x['stopPrice']))

    config.all_orders = orders

    print('\n' , 'total order ' , len(config.all_orders))
    for x in config.all_orders:
        print('order ID ' , x['orderId'] , ' | ', ' side ' , x['side'] , ' price ' , x['stopPrice'] , ' | ' , ' reduceOnly ' , x['reduceOnly'] )

def save_orders_status_1to3_json():

    index = [x['reduceOnly'] for x in config.all_orders].index(False)
    
    if config.all_orders[index]['side'] == 'BUY':
        config.order_status =[
            {"price":config.all_orders[index+1]['stopPrice'],"orderId":config.all_orders[index+1]['orderId']},
            {"price":config.all_orders[index+2]['stopPrice'],"orderId":config.all_orders[index+2]['orderId']}]
    else:
        config.order_status =[
            {"price":config.all_orders[index-1]['stopPrice'],"orderId":config.all_orders[index-1]['orderId']},
            {"price":config.all_orders[index-2]['stopPrice'],"orderId":config.all_orders[index-2]['orderId']}]
    print('\njson status')
    print(config.order_status)
def save_orders_status_other_json():

    index = [x['reduceOnly'] for x in config.all_orders].index(False)

    if config.all_orders[index]['side'] == 'BUY':
        config.order_status ={"price":config.all_orders[index+1]['stopPrice'],"orderId":config.all_orders[index+1]['orderId']}
    else:
        config.order_status ={"price":config.all_orders[index-1]['stopPrice'],"orderId":config.all_orders[index-1]['orderId']}
        
    print('\njson status')
    print(config.order_status)
        
def check_hit_SL_TP(symbol):
    client = Client(API_KEY, API_SECRET)

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
        index = [x['reduceOnly'] for x in config.all_orders].index(False)
        if config.all_orders[index]['side'] == 'BUY':
            check_sl_order = [x['orderId'] for x in orders].index(config.all_orders[index-1]['orderId'])

        else:
            check_sl_order = [x['orderId'] for x in orders].index(config.all_orders[index+1]['orderId'])

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
    print(config.order_status)

    orders = client.futures_get_open_orders(symbol=symbol)

    if config.type_tp == '1to3':
        try:
            print('check TP order id ', config.order_status[index]['orderId'])
            check_sl_order = [x['orderId'] for x in orders].index(config.order_status[index]['orderId'])
            #print('index is ',check_sl_order)

        except Exception as e:
            return True
    else:
        try:
            print('check TP order id ', config.order_status['orderId'])
            check_sl_order = [x['orderId'] for x in orders].index(config.order_status['orderId'])
            #print('index is ',check_sl_order)
        except Exception as e:
            return True
    
    return False

def change_new_stoploss(symbol,index):
    print('Have change new stoploss!!')

    orders = client.futures_get_open_orders(symbol=symbol)

    try:
        main_index = [x['reduceOnly'] for x in config.all_orders].index(False)
        if config.all_orders[main_index]['side'] == 'BUY':
            client.futures_cancel_order(symbol=symbol, orderId=config.all_orders[main_index-1]['orderId'])
            print('Closed old SL order ',config.all_orders[main_index-1]['orderId'])
        else:
            client.futures_cancel_order(symbol=symbol, orderId=config.all_orders[main_index+1]['orderId'])
            print('Closed old SL order ',config.all_orders[main_index+1]['orderId'])
        
    except Exception as e:
        print("an exception occured - {}".format(e))
    if config.type_tp == '1to3':
        try:
            print('Replace new SL order')
            print('send order TP index ', index)
            main_index = [x['reduceOnly'] for x in config.all_orders].index(False)
            if config.all_orders[main_index]['side'] == 'BUY': #main_index['stopPrice'] config.order_status[index-1]['stopPrice']
                if index == 0:
                    config.neworder = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                    type="STOP_MARKET",stopPrice=config.all_orders[main_index]['stopPrice'], timeInForce=TIME_IN_FORCE_GTC,)
                else:
                    config.neworder = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                    type="STOP_MARKET",stopPrice=config.order_status[index-1]['stopPrice'], timeInForce=TIME_IN_FORCE_GTC,)
            elif config.all_orders[main_index]['side'] == 'SELL':
                if index == 0:
                    config.neworder = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
                    type="STOP_MARKET",stopPrice=config.all_orders[main_index]['stopPrice'], timeInForce=TIME_IN_FORCE_GTC,)
                else:
                    config.neworder = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
                    type="STOP_MARKET",stopPrice=config.order_status[index-1]['stopPrice'], timeInForce=TIME_IN_FORCE_GTC,)
            print('new stoploss price = ', config.order_status[index-1]['stopPrice'])
        except Exception as e:
            print("an exception occured - {}".format(e))

    else:
        try:
            print('Replace new SL order')
            main_index = [x['reduceOnly'] for x in config.all_orders].index(False)
            if config.all_orders[main_index]['side'] == 'BUY': #main_index['stopPrice']
                config.neworder = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                type="STOP_MARKET",stopPrice=config.order_status['stopPrice'], timeInForce=TIME_IN_FORCE_GTC,)
            elif config.all_orders[main_index]['side'] == 'SELL':
                config.neworder = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
                type="STOP_MARKET",stopPrice=config.order_status['stopPrice'], timeInForce=TIME_IN_FORCE_GTC,)
            print('new stoploss price = ', config.order_status['stopPrice'],)
        except Exception as e:
            print("an exception occured - {}".format(e))

    try:
        orders = client.futures_get_open_orders(symbol=symbol)
        index = [x['reduceOnly'] for x in config.all_orders].index(False)
        if config.all_orders[index]['side'] == 'BUY':
            sl_index = index-1
        else:
            sl_index = index+1
        
        print('sl_index ',sl_index)
        print('new SL order',config.neworder)
        new_orders_id = config.neworder['orderId']
        new_orders_price = config.neworder['stopPrice']
        config.all_orders[sl_index]['orderId'] = new_orders_id
        config.all_orders[sl_index]['stopPrice'] = new_orders_price
        config.all_orders.sort(key=lambda x: float(x['stopPrice']))
        print('\n' , 'total order ' , len(config.all_orders))
        for x in config.all_orders:
            print('order ID ' , x['orderId'] , ' | ', ' side ' , x['side'] , ' price ' , x['stopPrice'] , ' | ' , ' reduceOnly ' , x['reduceOnly'] )

        print('Finish change SL order id json')
    except Exception as e:
        print("an exception occured - {}".format(e))

def change_stoploss(symbol):

    if config.type_tp == '1to3': #risk/reward 1/3
        if config.current_tp == 1 and check_hit_TP(symbol,1) == True: 
            change_new_stoploss(symbol,1)
            config.current_tp = 2
        elif config.current_tp == 0 and check_hit_TP(symbol,0) == True: #เป้าแรก ทำกำไร25% ที่ 1/3
            change_new_stoploss(symbol,0)
            config.current_tp = 1
        else:
            print('dont have any change SL')
    elif config.type_tp == '1to2': #risk/reward 1/2
        if config.current_tp == 0 and check_hit_TP(symbol,0) == True: #เป้าแรก ทำกำไร25% ที่ 1/2
            change_new_stoploss(symbol,0)
            config.current_tp = 1
        else:
            print('dont have any change SL')
    elif config.type_tp == '1to1': #risk/reward 1/1
        if config.current_tp == 0 and check_hit_TP(symbol,0) == True: #เป้าแรก ทำกำไร25% ที่ 0.5/1
            print('check_hit_TP pass')
            change_new_stoploss(symbol,0)
            config.current_tp = 1
        else:
            print('dont have any change SL')
    else:
        print('error')
    
    print('change new TP | current TP is ',config.current_tp)

def calculate_balance(stoploss_percent,balance):
    if stoploss_percent >= 30:
        return int(balance/2)
    elif stoploss_percent >= 20:
        return int(balance/1.5)
    elif stoploss_percent >= 15:
        return int(balance/1.3 )
    else:
        return balance
def check_candle(symbol):
    if check_main_order_status(symbol) == True and check_position_status(symbol) == False:
        if config.candle_count < 5:
            config.candle_count = config.candle_count+1
        elif config.candle_count >= 5:
            config.candle_count = 0
            cancel_all_order(symbol)

def open_position(side, symbol, high, low, order_type=ORDER_TYPE_MARKET): 
    try:
        precision = 3
        precision2 = 2

        tick_price = float(low)
        low_price = float(floor(tick_price))

        tick_price = float(high)
        high_price = float(ceil(tick_price))

        stoploss_percent = float(((float(high_price) - float(low_price))/float(low_price))*100)
        stoploss_percent = float(round(stoploss_percent, precision2))

        print("stoploss % is ", stoploss_percent)

        if stoploss_percent >= 15:
            config.type_tp = '1to1'
        elif stoploss_percent >= 6:
            config.type_tp = '1to2'
        else:
            config.type_tp = '1to3'
        print('type take profit = ',config.type_tp)

        pre_balance = client.futures_account_balance()
        balance = int(float(pre_balance[1]['balance']))
        print('your balance is', balance, 'USDT')

        balance_quantity = calculate_balance(stoploss_percent,balance)

        print('position size is ', balance_quantity, 'USDT')

        amount = (balance_quantity/1.025) / float(high)
        quantity = float(round(amount, precision))
        
        quantity_tp = quantity/4
        quantity_tp = float(round(quantity_tp, precision))

        if config.type_tp == '1to3':
            if side == "BUY": tp1 = (high_price*stoploss_percent/100)+high_price
            else: tp1 = low_price - (low_price*stoploss_percent/100)
            tp1 = float(round(tp1, precision2))
            print('Take Profit 1 = ',tp1)

            if side == "BUY": tp2 = (high_price*(stoploss_percent*2)/100)+high_price
            else: tp2 = low_price - (low_price*(stoploss_percent*2)/100)
            tp2 = float(round(tp2, precision2))
            print('Take Profit 2 = ',tp2)

            if side == "BUY": final_tp = (high_price*(stoploss_percent*3)/100)+high_price
            else: final_tp = low_price - (low_price*(stoploss_percent*3)/100)
            final_tp = float(round(final_tp, precision2))
            print('Take Profit 3 = ',final_tp)

        if config.type_tp == '1to2':
            if side == "BUY": tp1 = (high_price*stoploss_percent/100)+high_price
            else: tp1 = low_price - (low_price*stoploss_percent/100)
            tp1 = float(round(tp1, precision2))
            print('Take Profit 1 = ',tp1)

            if side == "BUY": final_tp = (high_price*(stoploss_percent*2)/100)+high_price
            else: final_tp = low_price - (low_price*(stoploss_percent*2)/100)
            final_tp = float(round(final_tp, precision2))
            print('Take Profit 2 = ',final_tp)

        if config.type_tp == '1to1':
            if side == "BUY": tp1 = (high_price*(stoploss_percent/2)/100)+high_price
            else: tp1 = low_price - (low_price*(stoploss_percent/2)/100)
            tp1 = float(round(tp1, precision2))
            print('Take Profit 1 = ',tp1)

            if side == "BUY": final_tp = (high_price*stoploss_percent/100)+high_price
            else: final_tp = low_price - (low_price*stoploss_percent/100)
            final_tp = float(round(final_tp, precision2))
            print('Take Profit 2 = ',final_tp)

        position_status = check_position_status(symbol)
        if position_status == True:
            print("position has ready!")
        else:
            print("position has not ready!")

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

                if config.type_tp == '1to3':
                    order = client.futures_create_order(symbol=symbol, side="SELL", reduceOnly="true",
                    type="TAKE_PROFIT_MARKET",stopPrice=tp2, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                type="TAKE_PROFIT_MARKET",stopPrice=final_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="SELL", closePosition="true",
                type="STOP_MARKET",stopPrice=low_price, timeInForce=TIME_IN_FORCE_GTC,)

                save_orders_json(symbol)
                if config.type_tp == '1to3':
                    save_orders_status_1to3_json()
                else:
                    save_orders_status_other_json()

                clear_current_tp()

            elif side == "SELL":
                order = client.futures_create_order(symbol=symbol, side=side,
                type="STOP_MARKET",stopPrice=low_price, quantity=quantity, timeInForce=TIME_IN_FORCE_GTC,)
                
                order = client.futures_create_order(symbol=symbol, side="BUY", reduceOnly="true",
                type="TAKE_PROFIT_MARKET",stopPrice=tp1, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                if config.type_tp == '1to3':
                    order = client.futures_create_order(symbol=symbol, side="BUY", reduceOnly="true",
                    type="TAKE_PROFIT_MARKET",stopPrice=tp2, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
                type="TAKE_PROFIT_MARKET",stopPrice=final_tp, quantity=quantity_tp, timeInForce=TIME_IN_FORCE_GTC,)

                order = client.futures_create_order(symbol=symbol, side="BUY", closePosition="true",
                type="STOP_MARKET",stopPrice=high_price, timeInForce=TIME_IN_FORCE_GTC,)
                save_orders_json(symbol)
                if config.type_tp == '1to3':
                    save_orders_status_1to3_json()
                else:
                    save_orders_status_other_json()

                clear_current_tp()
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