from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *
from ibapi.common import TickerId
from datetime import datetime, time
from threading import Thread
import time as time_module

class OpeningRangeHigh(EClient, EWrapper): 
    def __init__(self, stock_symbols):
        EClient.__init__(self, self)
        self.symbols = stock_symbols
        self.contracts = {}
        self.ticker_data = {}
        self.testFlow = True
        self.next_order_id = 1

        for i, symbol in enumerate(stock_symbols):
            self.ticker_data[i] = {
                'symbol': symbol['symbol'],
                'positionSize': symbol['positionSize'],
                'open': None,
                'high': float('-inf'),
                'low': float('inf'),
                'close': None,
                'breakout_triggered': False
            }
        print(f'this is tickers = ', self.ticker_data)

    def nextValidId(self, orderId):
        self.next_order_id = orderId
        print(f"Next valid order ID: {orderId}")

        for tickerId, symbol in self.ticker_data.items():
            print(f'symbol[symbol] = {symbol['symbol']}')
            contract = self.create_contract(symbol['symbol'])
            self.contracts[tickerId] = contract
            self.reqMktData(tickerId, contract, '', False, False, [])
    
    def create_contract(self, symbol):
        print(f'create contract symbol = {symbol}')
        contract = Contract()
        contract.symbol = symbol
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        return contract
    
    def inOpeningRange(self, now):
        if self.testFlow:
            return True
        else:
            return time(23, 30) <= now.time() < time(23, 45)

    def isMarketOpen(self, now):
        if self.testFlow:
            return True
        else:
            return time(23, 30) <= now.time() < time(6)
    
    # field is equal to tickType
    def tickPrice(self, tickerId: TickerId, field, price: float, attrib):
        now = datetime.now()
        data = self.ticker_data[tickerId]

        if price <= 0 or field != 2:
            return  # Invalid price

        if not self.isMarketOpen(now):
            print(f'market is close, come back later. current time: {now.time()}')
        if self.inOpeningRange(now): # need to add condition for field/tickType
            if data['open'] is None:
                data['open'] = price
            data['high'] = max(data['high'], price)
            data['low'] = min(data['low'], price)
            data['close'] = price
        elif self.isMarketOpen(now) and not data['breakout_triggered']:
            # Begin monitoring for breakout
            if price > data['high']:
                print(f"\n🚀 {data['symbol']} breakout above opening range at {price:.2f}")
                # self.place_bracket_order(tickerId, price, data['symbol'])

                data['breakout_triggered'] = True
        print(f'data = {data}')
        print(f'self.tickers = {self.ticker_data[tickerId]}')
    
    def place_bracket_order(self, tickerId, symbol, entry_price):
        # calculate quantity
        position = self.ticker_data[tickerId]['positionSize']
        numOfShares = int(position / entry_price)
        print(f'entering purchase order to buy {numOfShares} of {self.ticker_data[tickerId]} at {entry_price}')


        parent = Order()
        parent.orderId = self.next_order_id
        parent.action = "BUY"
        parent.orderType = "MKT"
        parent.totalQuantity = numOfShares
        parent.transmit = False

        take_profit = Order()
        take_profit.orderId = self.next_order_id + 1
        take_profit.action = "SELL"
        take_profit.orderType = "LMT"
        take_profit.totalQuantity = numOfShares
        take_profit.lmtPrice = round(entry_price * 1.05, 2)
        take_profit.parentId = parent.orderId
        take_profit.transmit = False

        stop_loss = Order()
        stop_loss.orderId = self.next_order_id + 2
        stop_loss.action = "SELL"
        stop_loss.orderType = "STP"
        stop_loss.auxPrice = round(entry_price * 0.95, 2)
        stop_loss.totalQuantity = numOfShares
        stop_loss.parentId = parent.orderId
        stop_loss.transmit = True

        contract = self.contracts[tickerId]

        self.placeOrder(parent.orderId, contract, parent)
        self.placeOrder(take_profit.orderId, contract, take_profit)
        self.placeOrder(stop_loss.orderId, contract, stop_loss)

        self.next_order_id += 3

        


def run_bot(symbols):
    livePort = 7496
    paperTradePort = 7497
    app = OpeningRangeHigh(symbols)
    app.connect('127.0.0.1', livePort, clientId=1)


    def run_loop():
        app.run()

    thread = Thread(target=app.run)
    thread.start()
    time_module.sleep(1)
    # thread = threading.Thread(target=run_loop, daemon=True)
    # thread.start()

    # while True:
    #     time_module.sleep(1)

if __name__ == '__main__':
    # run_bot(["RRGB", "TIRX", ])
    run_bot([
        {
            'symbol': 'RRGB',
            'positionSize': 700
        },
        {
            'symbol': 'TIRX',
            'positionSize': 900
        },
        {
            'symbol': 'TSM',
            'positionSize': 300
        }
    ])

