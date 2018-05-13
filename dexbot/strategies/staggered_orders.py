from math import sqrt
import collections

from dexbot.basestrategy import BaseStrategy
from dexbot.queue.idle_queue import idle_add

from bitshares.amount import Amount

NiceOrder = collections.namedtuple('NiceOrder', 'id typ price amount')


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
                "range",
                "float",
                0,
                "Range of lowest/highest prices from the startprice, in powers of two. So 1 = 2 x to 0.5 x, 2 = 4x to 0.25x, and so on.",
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
        self.spread = self.worker['spread'] / 100.0
        self.increment = self.worker['increment'] / 100.0
        self.upper_bound = None
        self.lower_bound = None
        self.start = self.worker['start'] / 100.0
        import pdb
        pdb.set_trace()
        self.updated_open_orders
        self.update_orders(self.calculate_center_price())

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
        startprice = bid + ((ask - bid) * self.start)
        if self.upper_bound is None:
            self.upper_bound = startprice * (2**self.worker['range'])
            self.lower_bound = startprice * (2**-self.worker['range'])
        return startprice

    def log_order(self, typ, amount, price):
        self.log.info("{typ} order {amt:.4g} {quote} at {price:.4g} {base}/{quote} (= {inv_price:.4g} {quote}/{base})".format(
            typ=typ,
            amt=amount,
            price=price,
            inv_price=1 / price,
            quote=self.market['quote']['symbol'],
            base=self.market['base']['symbol']))

    def nice_order_list(self):
        """
        Get list of orders in a nicer format
        the tuple (id, type, price, quote_amount)
        """
        for o in self.orders:
            id = o['id']
            if o['quote']['asset']['symbol'] == self.market['quote']['symbol']:
                typ = 'BUY'
                price = 1 / o['price']
                amount = float(o['quote'])
            else:
                typ = 'SELL'
                price = o['price']
                amount = float(o['base'])
            yield NiceOrder(id, typ, price, amount)

    def prices_close(self, price1, price2):
        """Return True if two prices are within increment / 2 of
        each other"""
        return abs(price1 - price2) / ((price1 + price2) / 2) <= self.increment / 2

    def update_orders(self, center_price):
        if center_price is None:
            return
        self.log.info("Centre price is {}".format(center_price))

        current_orders = list(self.nice_order_list())
        buy_orders = []
        buy_price = center_price * (1 - (self.spread / 2))

        buy_balance = float(self.balance(self.market['base']))
        buy_amount = buy_balance * self.increment

        buy_orders.append((buy_price, buy_amount / buy_price))
        while buy_price > self.lower_bound:
            buy_price = buy_price / (1 + self.increment)
            buy_amount = buy_amount * sqrt(1 + self.increment)
            found_order = False
            for o in current_orders:
                if o.typ == 'BUY' and self.prices_close(buy_price, o.price):
                    found_order = True
                    break
            if found_order:
                break
            else:
                buy_orders.append((buy_price, buy_amount / buy_price))

        buy_orders.reverse()  # enter outermost first

        for price, amount in buy_orders:
            self.log_order('BUY', amount, price)
            self.market.buy(price, Amount(amount, self.market['quote']), account=self.account)

        sell_orders = []
        sell_price = center_price * (1 + (self.spread / 2))

        sell_balance = float(self.balance(self.market['quote']))
        sell_amount = sell_balance * self.increment

        sell_orders.append((sell_price, sell_amount))

        while sell_price < self.upper_bound:
            sell_price = sell_price * (1 + (self.increment / 100.0))
            sell_amount = sell_amount / sqrt(1 + (self.increment / 100.0))
            found_order = False
            for o in current_orders:
                if o.typ == 'SELL' and self.prices_close(sell_price, o.price):
                    found_order = True
                    break
            if found_order:
                break
            else:
                sell_orders.append((sell_price, sell_amount))

        sell_orders.reverse()  # enter outermost first

        for price, amount in sell_orders:
            self.log_order('SELL', amount, price)
            self.market.sell(price, Amount(amount, self.market['quote']), account=self.account)

    def check_orders(self, *args, **kwargs):
        """ Tests if the orders need updating
        """

        self.update_orders(self.calculate_center_price())

        if self.view:
            self.update_gui_profit()
            self.update_gui_slider()

    # GUI updaters
    def update_gui_profit(self):
        pass

    def update_gui_slider(self):
        pass
