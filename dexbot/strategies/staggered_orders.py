from math import sqrt

from dexbot.basestrategy import BaseStrategy
from dexbot.queue.idle_queue import idle_add

from bitshares.amount import Amount


class Strategy(BaseStrategy):
    """ Staggered Orders strategy
    """

    @classmethod
    def configure(kls):
        return BaseStrategy.configure()+[
            ConfigElement(
                "spread",
                "float",
                5,
                "Percentage difference between buy and sell",
                (0, 100)),
            ConfigElement(
                "increment",
                "float",
                1,
                "Percentage difference between each stagger",
                (0, 100)),
            ConfigElement(
                "lower_bound",
                "float",
                0,
                "Lowest price in the ladder",
                (0, None)),
            ConfigElement(
                "upper_bound",
                "float",
                0,
                "Highest price in the ladder",
                (0, None)),
            ConfigElement(
                "start",
                "float",
                50.0,
                "Starting price, as percentage of bid/ask spread",
                (0.0, 100.0)),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define Callbacks
        #self.onMarketUpdate += self.check_orders
        #self.onAccount += self.check_orders

        self.error_ontick = self.error
        self.error_onMarketUpdate = self.error
        self.error_onAccount = self.error

        self.worker_name = kwargs.get('name')
        self.view = kwargs.get('view')
        self.spread = self.worker['spread']
        self.increment = self.worker['increment']
        self.upper_bound = self.worker['upper_bound']
        self.lower_bound = self.worker['lower_bound']
        self.start = self.worker['start']

        # for now just wipe the slate when we start
        self.cancel_all()
        self.init_strategy()

    def error(self, *args, **kwargs):
        self.cancel_all()
        self.disabled = True
        self.log.info(self.execute())

    def calculate_center_price(self):
        # for now using same algo as Follow Orders
        t = self.market.ticker()
        if t['highestBid'] is None:
            self.log.critical("no bid price available")
            self.disabled = True
            return None
        if t['lowestAsk'] is None or t['lowestAsk'] == 0.0:
            self.log.critical("no ask price available")
            self.disabled = True
            return None
        bid = float(t['highestBid'])
        ask = float(t['lowestAsk'])
        return bid + ((ask - bid) * self.start / 100.0)

    def log_order(self, typ, amount, price):
        self.log.info("{typ} order {amt:.4g} {quote} at {price:.4g} {base}/{quote} (= {inv_price:.4g} {quote}/{base})".format(
            typ=typ,
            amt=amount,
            price=price,
            inv_price=1 / price,
            quote=self.market['quote']['symbol'],
            base=self.market['base']['symbol']))

    def init_strategy(self):
        center_price = self.calculate_center_price()
        if center_price is None:
            return
        self.log.info("Centre price is {}".format(center_price))
        buy_orders = []
        buy_price = center_price * (1 - (self.spread / 200.0))

        buy_balance = 100.0  # currently pretend
        buy_amount = buy_balance * self.increment / 100.0

        buy_orders.append((buy_price, buy_amount / buy_price))
        self.log_order('BUY', buy_amount / buy_price, buy_price)
        while buy_price > self.lower_bound:
            buy_price = buy_price / (1 + (self.increment / 100.0))
            buy_amount = buy_amount * sqrt(1 + (self.increment / 100.0))
            buy_orders.append((buy_price, buy_amount / buy_price))
            self.log_order('BUY', buy_amount / buy_price, buy_price)

        sell_orders = []
        sell_price = center_price * (1 + (self.spread / 200.0))

        sell_balance = 100.0  # pretend
        sell_amount = sell_balance * self.increment / 100.0

        sell_orders.append((sell_price, sell_amount))
        self.log_order('SELL', sell_amount, sell_price)

        while sell_price < self.upper_bound:
            sell_price = sell_price * (1 + (self.increment / 100.0))
            sell_amount = sell_amount / sqrt(1 + (self.increment / 100.0))
            sell_orders.append((sell_price, sell_amount))
            self.log_order('SELL', sell_amount, sell_price)

        self['orders'] = []

    def update_order(self, order, order_type):
        self.log.info('Change detected, updating orders')
        # Make sure
        self.cancel(order)

        if order_type == 'buy':
            amount = order['quote']['amount']
            price = order['price'] * self.spread
            new_order = self.market_sell(amount, price)
        else:
            amount = order['base']['amount']
            price = order['price'] / self.spread
            new_order = self.market_buy(amount, price)

        self['orders'] = new_order

    def check_orders(self, *args, **kwargs):
        """ Tests if the orders need updating
        """
        for order in self['sell_orders']:
            current_order = self.get_updated_order(order)
            if current_order['quote']['amount'] != order['quote']['amount']:
                self.update_order(order, 'sell')

        for order in self['buy_orders']:
            current_order = self.get_updated_order(order)
            if current_order['quote']['amount'] != order['quote']['amount']:
                self.update_order(order, 'buy')

        if self.view:
            self.update_gui_profit()
            self.update_gui_slider()

    # GUI updaters
    def update_gui_profit(self):
        pass

    def update_gui_slider(self):
        pass
