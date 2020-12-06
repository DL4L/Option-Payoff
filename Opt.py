from yahoo_fin import options
from yahoo_fin import stock_info
import pandas as pd
from bisect import bisect_left, bisect_right
import datetime  
from pytz import timezone

class Stock():

    def __init__ (self,date=None):

        self.ticker = "SPY"
        self.date = date
        self.underlying = self.get_underlying_price()
        self.tickers_select = [{"label":i,"value":i} for i in stock_info.tickers_dow()] + [{"label": "SPY", "value": "SPY"}]
        

    def update_ticker(self,ticker):
        self.ticker = ticker
        self.underlying = self.get_underlying_price()
    def get_underlying(self,start_date=None,end_date=None):

        return stock_info.get_data(self.ticker,start_date,end_date)

    def get_underlying_price(self,start_date=None,end_date=None):

        return round(stock_info.get_live_price(self.ticker),2)
    
    def get_options_expirations(self):
        return [{"label":i,"value":i} for i in options.get_expiration_dates(self.ticker)]
        
    def get_options_chain(self,expiry_date=None):
        """
        Extracts call / put option tables for input ticker and expiration date.  If
        no date is input, the default result will be the earliest expiring
        option chain from the current date.

        @param: date
        """
        return options.get_options_chain(self.ticker,expiry_date)

    def get_calls_and_puts_formated(self,expiry_date=None):
        
        chain = options.get_options_chain(self.ticker,expiry_date)
        calls = chain['calls']
        
        c_strike_idx = self.get_closests(calls,"Strike",self.underlying)
        print("c_idx: ", c_strike_idx, "len: ", len(calls))
        c_range_lower = max(0,c_strike_idx - (len(calls)-c_strike_idx))
        calls = calls[c_range_lower:]
        calls.reset_index(inplace=True,drop=True)
        calls = calls[["Strike","Change","% Change","Bid","Ask","Last Price"]]

        
        #calls = calls[max(0,c_strike_idx-10):min(len(calls),c_strike_idx+11)]
        puts = chain['puts']
        
        p_strike_idx = self.get_closests(puts,"Strike",self.underlying)
        print("p_idx: ", p_strike_idx,  "len: ", len(puts))
        p_range_lower = max(0,p_strike_idx - (len(puts)-p_strike_idx))
        puts = puts[p_range_lower:].reset_index()
        puts = puts[["Strike","Change","% Change","Bid","Ask"]]
        print("Underlying Check",self.underlying)
        new_c_strike_index,new_p_strike_index = self.get_closests(calls,"Strike",self.underlying),self.get_closests(puts,"Strike",self.underlying)
        #puts = puts[max(0,p_strike_idx-10):min(len(puts),p_strike_idx+11)]

       # et_time = datetime.datetime.now(timezone('US/Eastern'))
       # fmt = "%H"
       # hour = et_time.strftime(fmt)
       # if int(hour) < 10:
       #     pass

        self.calls_formatted = calls
        self.puts_formatted = puts
        return calls,puts,new_c_strike_index,new_p_strike_index

    def get_closests(self,df, col, val):
        lower_idx = bisect_left(df[col].values, val)
        higher_idx = bisect_right(df[col].values, val)
        if higher_idx == lower_idx:      #val is not in the list
            if abs(val - df[col].iloc[lower_idx]) <= abs(val - df[col].iloc[lower_idx - 1]): # return index closest to val
                return lower_idx
            else:
                return lower_idx - 1
            
        else:                            #val is in the list
            return lower_idx

class Strategies():

    def __init__ (self):

        self.strategies_select = [{"label": "Long Strangle", "value": "Long Strangle"},
        {"label": "Straddle", "value": "Straddle"},
        {"label": "Iron Condor", "value": "Iron Condor"},
        ]

        self.strategies_descs = {"Long Strangle":{'desc':'Buy a call and a put option with different strike prices, but with the same expiration and underlying. A strangle is a good strategy if you think the underlying security will experience a large price movement in the near future but are unsure of the direction.The risk on the trade is limited to the premium paid for the two options.',
                                'action':["Buy an OTM call","Buy an OTM put"]},
        "Straddle":{'desc':'Buy a put and call ATM with the same strike price and expiration. A long straddle profits when the price of the security rises or falls from the strike price by an amount more than the total cost of the premium paid.','action':["Buy an ATM put", "Buy an ATM call"]},
        "Iron Condor":{'desc':'An iron condor consists of two puts (one long and one short) and two calls (one long and one short), and four strike prices, all with the same expiration. The goal is to profit from low volatility in the underlying asset. It earns the maximum profit when the underlying asset closes between the middle strike prices at expiration',
        'action':["Buy one OTM put with a strike price below the price of the underlying",
                                            "Sell one OTM or ATM put with a strike price closer to the price of the underlying",
                                            "Sell one OTM or ATM call with a strike price above the current price of the underlying asset",
                                            "Buy one OTM call with a strike price further above the current price of the underlying asset"]},
                                            }
        self.direction = '1'

        self.strategies_map = {1:self.long_call,2:self.long_put,3:self.short_call,4:self.short_put}

        self.current = {"Buy":{"Calls":set(),     #### Use either self.current nested dict or self.current_portfolio structure of options objects
                                "Puts":set()},
                        "Sell":{"Calls":set(),
                                "Puts":set()}}

        self.current_portfolio = {}
    def reset(self):
        self.direction = '1'

        self.strategies_map = {1:self.long_call,2:self.long_put,3:self.short_call,4:self.short_put}

        self.current = {"Buy":{"Calls":set(),     #### Use either self.current nested dict or self.current_portfolio structure of options objects
                                "Puts":set()},
                        "Sell":{"Calls":set(),
                                "Puts":set()}}

        self.current_portfolio = {}
    # S = stock underlying # K = strike price # Price = premium paid for option 
    def long_call(self,S, K, Price):
        # Long Call Payoff = max(Stock Price - Strike Price, 0)     # If we are long a call, we would only elect to call if the current stock price is greater than     # the strike price on our option     
        P = list(map(lambda x: max(x - K, 0) - Price, S))
        return P

    def long_put(self,S, K, Price):
        # Long Put Payoff = max(Strike Price - Stock Price, 0)     # If we are long a call, we would only elect to call if the current stock price is less than     # the strike price on our option     
        P = list(map(lambda x: max(K - x,0) - Price, S))
        return P
    
    def short_call(self,S, K, Price):
        # Payoff a shortcall is just the inverse of the payoff of a long call     
        P = self.long_call(S, K, Price)
        return [-1.0*p for p in P]

    def short_put(self,S,K, Price):
        # Payoff a short put is just the inverse of the payoff of a long put 
        P = self.long_put(S,K, Price)
        return [-1.0*p for p in P]
    
    def update_current(self, direction, contract_type, contract_idx):
        """
        """
        self.current[direction][contract_type].add(contract_idx)
        print("strategy_dict: ",self.current)

    def strategy_selector(self):

        strats = [{"label": "Long Call", "value": self.long_call(S,K, Price)}]

    def create_option(self,direction,contract_type,strike,price,option_id,underlying):

        option = Option(direction,contract_type,strike,price,option_id,underlying)
        return option
    
    def add_option_to_portfolio(self,option):
        self.current_portfolio[option.option_id] = option

    def remove_option_from_portfolio(self,option_id):
        del self.current_portfolio[option_id]

    def option_to_text(self,option):

        res = "%s $%s %s AT $%s"%(option.direction, option.strike, option.contract_type, option.price)
        return res

    
    def calculate_portfolio_payoff(self):
        """
        enumerate portfolio of options objects
        using the option object's direction and contract type can choose which function to map it to
        return the sum of the outputs of the functions as list
        e.g return [x+y for x,y in zip(F_1, F_2)]  or list(map(sum,zip(*[l1,l2,l3])))
        """
        lists = []
        port_map = {"BC":1,"BP":2,"SC":3,"SP":4}

        for opt_id in self.current_portfolio:
            prefix = opt_id.split('_')[0]
            option = self.current_portfolio[opt_id]
            S = [p for p in range(0,int(option.underlying*2))]
            print("option %s, strike type: %s, price type: %s"%(option.option_id,type(option.strike),type(option.price)))
            res = self.strategies_map[port_map[prefix]](S,option.strike,option.price)
            lists.append(res)
        
        result = list(map(sum,zip(*lists)))
        return result
        #print("Payoff: ", result)

class Option():

    def __init__ (self,direction,contract_type,strike,price,option_id,underlying):
        """
        price = cost or premium. Maybe split into 2 params

        option_id for keeping track and deletions - may not be necessary
        """
        self.direction = direction
        self.contract_type = contract_type
        self.strike = float(strike)
        self.price = float(price)
        self.option_id = option_id
        self.underlying = float(underlying)