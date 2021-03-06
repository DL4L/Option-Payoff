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

from Stock import *


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
def calc_gamma(S, K, r, vol, T, t, otype):
    d1 = d1_calc(S, K, r, vol, T, t)
    gamma = (norm.pdf(d1)) / (S * vol * np.sqrt(T-t))
    return gamma

def calc_vega(S, K, r, vol, T, t, otype):
    d1 = d1_calc(S, K, r, vol, T, t)
    return S * norm.pdf(d1) * np.sqrt(T-t)

def calc_theta(S, K, r, vol, T, t, otype):
    d1 = d1_calc(S, K, r, vol, T, t)
    d2 = d1 - vol*np.sqrt(T-t)
    
    if(otype == "call"):
        theta = -(S*norm.pdf(d1)*vol / (2*np.sqrt(T-t))) - r*K*np.exp(-r*(T-t))*norm.cdf(d2) 
    elif(otype == "put"):
        theta = -(S*norm.pdf(d1)*vol / (2*np.sqrt(T-t))) + r*K*np.exp(-r*(T-t))*norm.cdf(-d2)

    return theta
class Strategies():

    def __init__(self):

        self.strategies_select = [{"label": "Long Strangle", "value": "Long Strangle"},
                                  {"label": "Straddle", "value": "Straddle"},
                                  {"label": "Iron Condor", "value": "Iron Condor"},
                                  ]

        self.strategies_descs = {"Long Strangle": {'desc': 'Buy a call and a put option with different strike prices, but with the same expiration and underlying. A strangle is a good strategy if you think the underlying security will experience a large price movement in the near future but are unsure of the direction.The risk on the trade is limited to the premium paid for the two options.',
                                                   'action': ["Buy an OTM call", "Buy an OTM put"]},
                                 "Straddle": {'desc': 'Buy a put and call ATM with the same strike price and expiration. A long straddle profits when the price of the security rises or falls from the strike price by an amount more than the total cost of the premium paid.', 'action': ["Buy an ATM put", "Buy an ATM call"]},
                                 "Iron Condor": {'desc': 'An iron condor consists of two puts (one long and one short) and two calls (one long and one short), and four strike prices, all with the same expiration. The goal is to profit from low volatility in the underlying asset. It earns the maximum profit when the underlying asset closes between the middle strike prices at expiration',
                                                 'action': ["Buy one OTM put with a strike price below the price of the underlying",
                                                            "Sell one OTM or ATM put with a strike price closer to the price of the underlying",
                                                            "Sell one OTM or ATM call with a strike price above the current price of the underlying asset",
                                                            "Buy one OTM call with a strike price further above the current price of the underlying asset"]},

                                 }
        self.direction = '1'

        self.strategies_map = {
            1: self.long_call, 2: self.long_put, 3: self.short_call, 4: self.short_put}

        self.current = {"Buy": {"Calls": set(),  # Use either self.current nested dict or self.current_portfolio structure of options objects
                                "Puts": set()},
                        "Sell": {"Calls": set(),
                                 "Puts": set()}}

        self.current_portfolio = {}

    def reset(self):
        self.direction = '1'

        self.current = {"Buy": {"Calls": set(),  # Use either self.current nested dict or self.current_portfolio structure of options objects
                                "Puts": set()},
                        "Sell": {"Calls": set(),
                                 "Puts": set()}}

        self.current_portfolio = {}
    # S = stock underlying # K = strike price # Price = premium paid for option

    def long_call(self, S, K, Price):
        # Long Call Payoff = max(Stock Price - Strike Price, 0)     # If we are long a call, we would only elect to call if the current stock price is greater than     # the strike price on our option
        P = list(map(lambda x: max(x - K, 0) - Price, S))
        return P

    def long_put(self, S, K, Price):
        # Long Put Payoff = max(Strike Price - Stock Price, 0)     # If we are long a call, we would only elect to call if the current stock price is less than     # the strike price on our option
        P = list(map(lambda x: max(K - x, 0) - Price, S))
        return P

    def short_call(self, S, K, Price):
        # Payoff a shortcall is just the inverse of the payoff of a long call
        P = self.long_call(S, K, Price)
        return [-1.0*p for p in P]

    def short_put(self, S, K, Price):
        # Payoff a short put is just the inverse of the payoff of a long put
        P = self.long_put(S, K, Price)
        return [-1.0*p for p in P]

    def update_current(self, direction, contract_type, contract_idx):
        """
        """
        self.current[direction][contract_type].add(contract_idx)
        print("strategy_dict: ", self.current)

    def strategy_selector(self):

        strats = [{"label": "Long Call", "value": self.long_call(S, K, Price)}]

    def create_option(self, direction, contract_type, strike, price, impvol, option_id, underlying):

        option = Option(direction, contract_type, strike,
                        price, impvol, option_id, underlying)
        return option

    def add_option_to_portfolio(self, option):
        self.current_portfolio[option.option_id] = option

    def remove_option_from_portfolio(self, option_id):
        del self.current_portfolio[option_id]

    def option_to_text(self, option):

        res = "%s $%s %s AT $%s" % (
            option.direction, option.strike, option.contract_type, option.price)
        return res

    def calculate_portfolio_payoff(self):
        """
        enumerate portfolio of options objects
        using the option object's direction and contract type can choose which function to map it to
        return the sum of the outputs of the functions as list
        e.g return [x+y for x,y in zip(F_1, F_2)]  or list(map(sum,zip(*[l1,l2,l3])))
        """
        lists = []
        port_map = {"BC": 1, "BP": 2, "SC": 3, "SP": 4}

        for opt_id in self.current_portfolio:
            prefix = opt_id.split('_')[0]
            option = self.current_portfolio[opt_id]
            S = [p for p in range(0, int(option.underlying*2))]
            print("option %s, strike type: %s, price type: %s" %
                  (option.option_id, type(option.strike), type(option.price)))
            res = self.strategies_map[port_map[prefix]](
                S, option.strike, option.price)
            lists.append(res)

        result = list(map(sum, zip(*lists)))
        return result
        #print("Payoff: ", result)

    def max_gain(self, payoff):

        max_p = max(payoff)

        if payoff[0] == max_p:  # Short Underlying
            if payoff[2] < payoff[1] < payoff[0]:
                return "Max Profit: Infinite"
            else:
                return "Max Profit: %s * 100 = %s" % (str(round(max_p, 2)), round(max_p*100, 2))
        elif payoff[-1] == max_p:  # Long Underlying
            if payoff[-3] < payoff[-2] < payoff[-1]:
                return "Max Profit: Infinite"
            else:
                return "Max Profit: %s * 100 = %s" % (str(round(max_p, 2)), round(max_p*100, 2))
        else:
            return "Max Profit: %s * 100 = %s" % (str(round(max_p, 2)), round(max_p*100, 2))

    def max_loss(self, payoff):

        max_l = min(payoff)

        if payoff[0] == max_l:  # Short Underlying
            if payoff[2] > payoff[1] > payoff[0]:
                return "Max Loss: Infinite"
            else:
                return "Max Loss: %s * 100 = %s" % (str(round(max_l, 2)), round(max_l*100, 2))
        elif payoff[-1] == max_l:  # Long Underlying
            if payoff[-3] > payoff[-2] > payoff[-1]:
                return "Max Loss: Infinite"
            else:
                return "Max Loss: %s * 100 = %s" % (str(round(max_l, 2)), round(max_l*100, 2))
        else:
            return "Max Loss: %s * 100 = %s" % (str(round(max_l, 2)), round(max_l*100, 2))

    def calculate_portfolio_greeks(self, curr_date, exp_date):
        
        result = {'delta':[],'gamma':[],'vega':[],'theta':[]}
        lists = []
        r = 0.01
        T = (parser.parse(exp_date) - curr_date).days/365
        for opt_id in self.current_portfolio:
            prefix = opt_id.split('_')[0]
            option = self.current_portfolio[opt_id]
            impvol = option.impvol.replace('%', '')
            impvol = float(impvol)/100
            S = [p for p in range(0, int(option.underlying*2))]
            
            gamma = np.asarray(
                    [calc_gamma(s, option.strike, r, impvol, T, 0, "call") for s in S]) ### gamma for call/put the same
            vega = np.asarray(
                    [calc_vega(s, option.strike, r, impvol, T, 0, "call") for s in S])

            if prefix[1] == "C":
                delta = np.asarray(
                    [calc_delta(s, option.strike, r, impvol, T, 0, "call") for s in S])
                theta = np.asarray(
                    [calc_theta(s, option.strike, r, impvol, T, 0, "call") for s in S])
            if prefix[1] == "P":
                delta = np.asarray(
                    [calc_delta(s, option.strike, r, impvol, T, 0, "put") for s in S])
                theta = np.asarray(
                    [calc_theta(s, option.strike, r, impvol, T, 0, "put") for s in S])
            if prefix[0] == "S":

                delta = delta*-1
                gamma = gamma*-1
                vega = vega*-1
                theta = theta*-1

            result['delta'].append(delta)
            result['gamma'].append(gamma)
            result['vega'].append(vega)
            result['theta'].append(theta)
            #lists.append(res)
        for key in result:
            result[key] = list(map(sum, zip(*result[key])))
        print("GREEK RES: ", result)
        return result

    # S: underlying stock price # K: Option strike price # r: risk free rate
    # # D: dividend value # vol: Volatility # T: time to expiry (assumed that we're measuring from t=0 to T)


class Option():

    def __init__(self, direction, contract_type, strike, price, impvol, option_id, underlying):
        """
        price = cost or premium. Maybe split into 2 params

        option_id for keeping track and deletions - may not be necessary
        """
        self.direction = direction
        self.contract_type = contract_type
        self.strike = float(strike)
        self.price = float(price)
        self.impvol = impvol
        self.option_id = option_id
        self.underlying = float(underlying)
