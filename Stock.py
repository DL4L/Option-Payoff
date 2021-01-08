
from yahoo_fin import options
from yahoo_fin import stock_info
import pandas as pd
from bisect import bisect_left, bisect_right
import datetime
from pytz import timezone
import pickle
from dateutil import parser
from scipy.stats import norm
import numpy as np

#from Opt import calc_delta, d1_calc


def d1_calc(S, K, r, vol, T, t):
    # Calculates d1 in the BSM equation
    return (np.log(S/K) + (r + 0.5 * vol**2)*(T-t))/(vol*np.sqrt(T-t))


def calc_delta(S, K, r, vol, T, t, otype):
    d1 = d1_calc(S, K, r, vol, T, t)
    d2 = d1 - vol * np.sqrt(T-t)

    if(otype == "call"):
        delta = np.exp(-(T-t))*norm.cdf(d1)
    elif(otype == "put"):
        delta = -np.exp(-(T-t))*norm.cdf(-d1)

    return round(delta, 2)


class Stock():

    def __init__(self, date=None):

        self.ticker = "AAPL"
        self.date = date
        self.expiry_date = None
        self.underlying = self.get_underlying_price()
        self.tickers_select = [{"label": i, "value": i} for i in stock_info.tickers_dow(
        )] + [{"label": "SPY", "value": "SPY"}]
        self.calls_formatted = None
        self.puts_formatted = None
        self.live_price = self.live_prices_released()

        if self.live_price:
            self.live_price_comment = ''
            self.current_date = datetime.datetime.now()
        else:
            self.live_price_comment = "* Prices displayed are not current. Live prices released around 3pm GMT"
            self.current_date = datetime.datetime(2021, 1, 7)

    def live_prices_released(self):
        et_time = datetime.datetime.now(timezone('US/Eastern'))
        fmt = "%H"
        hour = et_time.strftime(fmt)
        print("HOUR: ", hour)
        if int(hour) < 10:
            return False
        return True

    def update_expiry_date(self, expiry_date):
        print("Updating Expiry: ", expiry_date)
        self.expiry_date = expiry_date

    def update_ticker(self, ticker):
        self.ticker = ticker
        self.underlying = self.get_underlying_price()

    def get_underlying(self, start_date=None, end_date=None):

        return stock_info.get_data(self.ticker, start_date, end_date)

    def get_underlying_price(self, start_date=None, end_date=None):

        return round(stock_info.get_live_price(self.ticker), 2)

    def get_options_expirations(self):

        if not self.live_prices_released():
            filename = 'Chains/' + self.ticker + '_' + 'expirations.pickle'
            expirations = pickle.load(open(filename, "rb"))
        else:
            expirations = options.get_expiration_dates(self.ticker)
        return [{"label": i, "value": i} for i in expirations]

    def get_options_chain(self, expiry_date=None):
        """
        Extracts call / put option tables for input ticker and expiration date.  If
        no date is input, the default result will be the earliest expiring
        option chain from the current date.

        @param: date
        """
        return options.get_options_chain(self.ticker, expiry_date)

    def get_calls_and_puts_formated(self, expiry_date=None):

        if not self.live_prices_released():
            chain = self.get_calls_and_puts_formated_old_prices(expiry_date)
        else:
            chain = options.get_options_chain(self.ticker, expiry_date)

        calls = chain['calls']

        c_strike_idx = self.get_closests(calls, "Strike", self.underlying)
        print("c_idx: ", c_strike_idx, "len: ", len(calls))
        c_range_lower = max(0, c_strike_idx - (len(calls)-c_strike_idx))
        calls = calls[c_range_lower:]
        calls.reset_index(inplace=True, drop=True)
        calls = calls[["Strike", "Change", "% Change", "Bid",
                       "Ask", "Last Price", "Implied Volatility"]]
        call_deltas = self.get_deltas(calls, "call", expiry_date)
        calls['delta'] = call_deltas

        #calls = calls[max(0,c_strike_idx-10):min(len(calls),c_strike_idx+11)]
        puts = chain['puts']

        p_strike_idx = self.get_closests(puts, "Strike", self.underlying)
        print("p_idx: ", p_strike_idx,  "len: ", len(puts))
        p_range_lower = max(0, p_strike_idx - (len(puts)-p_strike_idx))
        puts = puts[p_range_lower:].reset_index()
        puts = puts[["Strike", "Change", "% Change",
                     "Bid", "Ask", "Implied Volatility"]]
        print("Underlying Check", self.underlying)
        new_c_strike_index, new_p_strike_index = self.get_closests(
            calls, "Strike", self.underlying), self.get_closests(puts, "Strike", self.underlying)
        #puts = puts[max(0,p_strike_idx-10):min(len(puts),p_strike_idx+11)]

        self.calls_formatted = calls.copy()
        self.puts_formatted = puts.copy()
        return calls, puts, new_c_strike_index, new_p_strike_index

    def get_calls_and_puts_formated_old_prices(self, expiry_date=None):

        filename = 'Chains/' + self.ticker + '_' + expiry_date + '.pickle'
        chain = pickle.load(open(filename, "rb"))
        return chain

    def get_closests(self, df, col, val):
        lower_idx = bisect_left(df[col].values, val)
        higher_idx = bisect_right(df[col].values, val)
        if higher_idx == lower_idx:  # val is not in the list
            # return index closest to val
            if abs(val - df[col].iloc[lower_idx]) <= abs(val - df[col].iloc[lower_idx - 1]):
                return lower_idx
            else:
                return lower_idx - 1

        else:  # val is in the list
            return lower_idx

    def get_deltas(self, df, otype, expiry_date):

        deltas = []
        T = (parser.parse(expiry_date) - self.current_date).days/365
        r = 0.01
        S = self.underlying
        for _, row in df.iterrows():
            K = row['Strike']
            vol = row['Implied Volatility'].replace('%', '')
            print(vol)
            vol = float(vol)/100
            # print(vol)

            deltas.append(calc_delta(S, K, r, vol, T, 0, otype))

        return deltas
