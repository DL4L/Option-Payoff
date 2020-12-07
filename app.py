import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio
from dash.dependencies import State, Input, Output, ALL
from dash.exceptions import PreventUpdate


from Opt import Stock, Strategies
import pandas as pd
import os
stock = Stock()
strategy = Strategies()
app = dash.Dash(
    __name__,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, maximum-scale=1.0, user-scalable=no",
        }
    ],
)
server = app.server

app.config["suppress_callback_exceptions"] = True



tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}



def build_upper_left_panel():
    return html.Div(
        id="upper-left",
        className="six columns select-area",
        children=[
            html.P(
                className="section-title",
                children="",
            ),
            html.Div(
                className="control-row-1",
                children=[
                    html.Div(
                        id="ticker-select-outer",
                        children=[
                            html.Label("Select a Ticker"),
                            dcc.Dropdown(
                                id="ticker-select",
                                options=stock.tickers_select,
                                value="AAPL",
                            ),
                        ],
                    ),
                    html.Div(
                        id="select-metric-outer",
                        children=[
                            html.Label("Choose an Expiry"),
                            dcc.Dropdown(
                                id="expiry-select",
                                #options=Stock.get_options_expirations(),
                               
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="region-select-outer",
                className="control-row-2",
                children=[
                    html.Label("Pick a Strategy"),
                    html.Div(
                        id="region-select-dropdown-outer",
                        children=dcc.Dropdown(
                            id="strategy-select", multi=False, searchable=True,
                            options=strategy.strategies_select
                        ),
                    ),
                ],
            ),
            html.Div(id="strategy-desc"),
            html.Ul(id="strategy-action"),
            html.Ul(id="dummy-output"),
            html.Ul(id="dummy-output-2"),
            
            html.Ul(id="dummy-input",hidden=True),
            html.Div(
                id="table-container",
                className="table-container",
                children=[
                    html.Div(
                        id="table-upper",
                        children=[
                            html.P(""),
                            html.P(id="underlying-price"),
                            html.Div(id="tabs-area-1",children = [dcc.Tabs(id='tabs-buy-sell', value='tab-buy', children=[
                            dcc.Tab(label='Buy', value='tab-buy',style=tab_style, selected_style=tab_selected_style),
                            dcc.Tab(label='Sell', value='tab-sell',style=tab_style, selected_style=tab_selected_style),
                            ],style = tabs_styles),]),
                            html.Div(id="tabs-area-2",children =[                            
                            dcc.Tabs(id='tabs-example', value='calls', children=[
                            dcc.Tab(label='Calls', value='calls',style=tab_style, selected_style=tab_selected_style),
                            dcc.Tab(label='Puts', value='puts',style=tab_style, selected_style=tab_selected_style),
                            ],style = tabs_styles)] ),
                            html.Div(id="moneyness",children=[
                            html.P("In the Money",id="itm"),
                            html.P("Out the Money",id="otm"),
                            html.P("At the Money",id="atm")
                            ]),
                            dcc.Loading(children=html.Div(id="buy-calls-stats-container")),
                            dcc.Loading(children=html.Div(id="sell-calls-stats-container")),
                            dcc.Loading(children=html.Div(id="buy-puts-stats-container")),
                            dcc.Loading(children=html.Div(id="sell-puts-stats-container")),
                            
                            #dash_table.DataTable(
                            #    id="option-chain-table"
                            #)

                        ],
                    ),

                    
                ],
            ),
        ],
    )




app.layout = html.Div(
    className="container scalable",
    children=[
        html.Div(
            id="banner",
            className="banner",
            children=[
                html.H6("Option Strategy & Payoff Calculator"),

            ],
        ),
        html.Div(
            id="upper-container",
            className="row",
            children=[
                build_upper_left_panel(),
                html.Div(
                    id="geo-map-outer",
                    className="six columns graph-area",
                    children=[
                        html.P(
                            id="map-title",
                            children="Option Payoff"
                            
                        ),
                        html.Div(
                            id="geo-map-loading-outer",
                            children=[
                                dcc.Loading(
                                    id="loading",
                                    children=dcc.Graph(
                                        id="option-payoff-graph",
                                    ),
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),

        
    ],
)

"""@app.callback([Output("buy-calls-stats-container","style")],
              Input('tabs-buy-sell', 'value'))
def render_content(tab):
    if tab == 'tab-buy':
        strategy.direction = '1'
        return {'display': 'block'}
    elif tab == 'tab-sell':
        strategy.direction = '-1'
        return {'display': 'none'}"""

@app.callback([Output("buy-calls-stats-container","style"),Output("sell-calls-stats-container","style"),
              Output("buy-puts-stats-container","style"),Output("sell-puts-stats-container","style")],
              [Input('tabs-example', 'value'), Input('tabs-buy-sell', 'value')])
def render_content(tab_pc,tab_bs):
    """
    order:  BUY CALL, SELL CALL, BUY PUT, SELL PUT
    """
    if tab_pc == 'calls':
        if tab_bs == 'tab-buy':
            strategy.direction = '1'
            return {'display': 'block'},{'display': 'none'},{'display': 'none'},{'display': 'none'}
        elif tab_bs == 'tab-sell':
            strategy.direction = '-1'
            return {'display': 'none'},{'display': 'block'},{'display': 'none'},{'display': 'none'}
    elif tab_pc == 'puts':
        if tab_bs == 'tab-buy':
            strategy.direction = '1'
            return {'display': 'none'},{'display': 'none'},{'display': 'block'},{'display': 'none'}
        elif tab_bs == 'tab-sell':
            strategy.direction = '-1'
            return {'display': 'none'},{'display': 'none'},{'display': 'none'},{'display': 'block'}


@app.callback([Output("expiry-select","options"),Output("expiry-select","value"),Output("underlying-price","children")],[
    Input("ticker-select","value")]
    )

def update_ticker(ticker):
    """
    After ticker is updated, populate expiry dropdown
    """
    stock.update_ticker(ticker)
    expirations = stock.get_options_expirations()
    expiry = expirations[0]["value"]
    #underlying = stock.get_underlying_price()
    underlying = "Underlying Price: %s"%(stock.underlying)
    strategy.reset()
    
    #print(expirations)
    return expirations,expiry,underlying

@app.callback([Output("buy-calls-stats-container","children"),Output("sell-calls-stats-container","children"),
Output("buy-puts-stats-container","children"),Output("sell-puts-stats-container","children")],
    [Input("expiry-select","value")]
    )
def update_expiry(expiry):
    calls,puts,c_strike_idx,p_strike_idx = stock.get_calls_and_puts_formated(expiry_date=expiry)
    strategy.reset()
    print("New strike indexes c & p: ", c_strike_idx,p_strike_idx, "type: ", type(c_strike_idx))
    print("pages c & p: ", c_strike_idx//17,p_strike_idx//17)
    print("update_expiry_func current portfolio", strategy.current_portfolio)
    #print("underlying price: ", stock.underlying)
    buy_calls_data_table = dash_table.DataTable(
        id="buy-call-stats-table",
        columns=[{"name": i, "id": i} for i in calls.columns],
        data=calls.to_dict('records'),
        #filter_action="native",
        row_selectable='multi',
        selected_rows=[],
        hidden_columns=[],
        page_size=17,
        page_current = (c_strike_idx//17),
        style_cell={"background-color": "#242a3b", "color": "#7b7d8d"},
        #style_as_list_view=False,
        style_header={"background-color": "#1f2536", "padding": "0px 5px"},
        style_data_conditional= [
        {
            'if': {
                'filter_query': '{Strike} = %s'%(calls["Strike"].iloc[c_strike_idx])
            },
            'backgroundColor': '#0074D9',
            'color': 'white'
        },
        {
            'if': {
                'filter_query': '{Strike} < %s'%(calls["Strike"].iloc[c_strike_idx])
            },
            'backgroundColor': 'green',
            'color': 'white'
        },
        {
            'if': {
                'filter_query': '{Strike} > %s'%(calls["Strike"].iloc[c_strike_idx])
            },
            'backgroundColor': 'red',
            'color': 'white'
        },
             
    ]
    )
    sell_calls_data_table = dash_table.DataTable(
        id="sell-call-stats-table",
        columns=[{"name": i, "id": i} for i in calls.columns],
        data=calls.to_dict('records'),
        #filter_action="native",
        row_selectable='multi',
        selected_rows=[],
        hidden_columns=[],
        page_size=17,
        page_current = (c_strike_idx//17),
        style_cell={"background-color": "#242a3b", "color": "#7b7d8d"},
        #style_as_list_view=False,
        style_header={"background-color": "#1f2536", "padding": "0px 5px"},
        style_data_conditional= [
        {
            'if': {
                'filter_query': '{Strike} = %s'%(calls["Strike"].iloc[c_strike_idx])
            },
            'backgroundColor': '#0074D9',
            'color': 'white'
        },
        {
            'if': {
                'filter_query': '{Strike} < %s'%(calls["Strike"].iloc[c_strike_idx])
            },
            'backgroundColor': 'green',
            'color': 'white'
        },
        {
            'if': {
                'filter_query': '{Strike} > %s'%(calls["Strike"].iloc[c_strike_idx])
            },
            'backgroundColor': 'red',
            'color': 'white'
        },
             
    ]
    )
    buy_puts_data_table = dash_table.DataTable(
        id="buy-puts-stats-table",
        columns=[{"name": i, "id": i} for i in puts.columns],
        data=puts.to_dict('records'),
        #filter_action="native",
        row_selectable='multi',
        selected_rows=[],
        page_size=17,
        page_current = (p_strike_idx//17),
        style_cell={"background-color": "#242a3b", "color": "#7b7d8d"},
        #style_as_list_view=False,
        style_header={"background-color": "#1f2536", "padding": "0px 5px"},
        style_data_conditional=[
        {
            'if': {
                'filter_query': '{Strike} = %s'%(puts["Strike"].iloc[p_strike_idx])
            },
            'backgroundColor': '#0074D9',
            'color': 'white'
            
        },
        {
            'if': {
                'filter_query': '{Strike} < %s'%(puts["Strike"].iloc[p_strike_idx])
            },
            'backgroundColor': 'red',
            'color': 'white'
        },
        {
            'if': {
                'filter_query': '{Strike} > %s'%(puts["Strike"].iloc[p_strike_idx])
            },
            'backgroundColor': 'green',
            'color': 'white'
        }
    ]
    )
    sell_puts_data_table = dash_table.DataTable(
        id="sell-puts-stats-table",
        columns=[{"name": i, "id": i} for i in puts.columns],
        data=puts.to_dict('records'),
        #filter_action="native",
        row_selectable='multi',
        selected_rows=[],
        page_size=17,
        page_current = (p_strike_idx//17),
        style_cell={"background-color": "#242a3b", "color": "#7b7d8d"},
        #style_as_list_view=False,
        style_header={"background-color": "#1f2536", "padding": "0px 5px"},
        style_data_conditional=[
        {
            'if': {
                'filter_query': '{Strike} = %s'%(puts["Strike"].iloc[p_strike_idx])
            },
            'backgroundColor': '#0074D9',
            'color': 'white'
            
        },
        {
            'if': {
                'filter_query': '{Strike} < %s'%(puts["Strike"].iloc[p_strike_idx])
            },
            'backgroundColor': 'red',
            'color': 'white'
        },
        {
            'if': {
                'filter_query': '{Strike} > %s'%(puts["Strike"].iloc[p_strike_idx])
            },
            'backgroundColor': 'green',
            'color': 'white'
        }
    ]
    )
    return buy_calls_data_table,sell_calls_data_table, buy_puts_data_table,sell_puts_data_table

@app.callback(
    Output("strategy-desc","children"),
    Output("strategy-action","children"),
    
   [ Input("strategy-select","value")])

def update_strategy(strat):
    if strat:
        
        desc = strategy.strategies_descs[strat]['desc']
        actions = strategy.strategies_descs[strat]['action']

        ret_desc = "Description: " + desc
        ret_actions = [html.Li(className="strategy-action",children=[item]) for item in actions]
    
        return ret_desc, ret_actions
    
    return '',[]

@app.callback(
    [Output("dummy-output","children"),Output("option-payoff-graph","figure")],
    [Input('buy-call-stats-table', 'selected_rows'),Input('sell-call-stats-table', 'selected_rows'),
    Input('buy-puts-stats-table', 'selected_rows'),Input('sell-puts-stats-table', 'selected_rows'),
    Input({'type':"delete",'index':ALL}, 'n_clicks'),Input("strategy-desc","children")]
)
def select_option_from_chain(buy_call_selected_rows,sell_call_selected_rows,buy_puts_selected_rows,sell_puts_selected_rows,n_clicks,strategy_state):
    
    ctx = dash.callback_context
    if strategy_state and 'strategy-desc' in ctx.triggered[0]["prop_id"]:
        print("STRAT")
        print("strategy state: ", ctx.triggered)
        strategy.reset()
        return '',{}
        #print("current state: ", output_state)

    if ctx.triggered and 'selected_rows' in ctx.triggered[0]["prop_id"]:
        print("trigger ", ctx.triggered)
        call_or_put = ctx.triggered[0]["prop_id"].split('.')[0]
        print("c or p",call_or_put)
        if call_or_put == "buy-call-stats-table":
            if buy_call_selected_rows:
                print("buy_call_selected_rows", buy_call_selected_rows)
                idx = buy_call_selected_rows[-1]
                row = stock.calls_formatted.iloc[idx]
                print("direction = ", strategy.direction)
                #print("Selected Row Data", row)
                if strategy.direction =='1':
                    #strategy.update_current("Buy","Calls",idx)
                    opt = strategy.create_option(strategy.direction,"call",row["Strike"],row["Ask"],"BC_%s"%(idx),stock.underlying)
                    strategy.add_option_to_portfolio(opt)
                    #return output_state + '\n' + strategy.direction + ' %s Call for %s '%(row["Strike"],row["Ask"])
        elif call_or_put == "sell-call-stats-table":
            if sell_call_selected_rows:
                print("sell_call_selected_rows", sell_call_selected_rows)
                idx = sell_call_selected_rows[-1]
                row = stock.calls_formatted.iloc[idx]
                print("direction = ", strategy.direction)
                if strategy.direction =='-1':
                    #strategy.update_current("Sell","Calls",idx)
                    opt = strategy.create_option(strategy.direction,"call",row["Strike"],row["Bid"],"SC_%s"%(idx),stock.underlying)
                    strategy.add_option_to_portfolio(opt)
                    #return output_state + '\n' + strategy.direction + ' %s Call for %s '%(row["Strike"],row["Bid"])

        elif call_or_put == "buy-puts-stats-table":
            if buy_puts_selected_rows:
                idx = buy_puts_selected_rows[-1]
                row = stock.puts_formatted.iloc[idx]
                
                #print("Selected Row Data", row)
                if strategy.direction =='1':
                    #strategy.update_current("Buy","Puts",idx)
                    opt = strategy.create_option(strategy.direction,"put",row["Strike"],row["Ask"],"BP_%s"%(idx),stock.underlying)
                    strategy.add_option_to_portfolio(opt)
                    #return output_state + strategy.direction + ' %s Put for %s '%(row["Strike"],row["Ask"])


        elif call_or_put == "sell-puts-stats-table":
            if sell_puts_selected_rows:
                idx = sell_puts_selected_rows[-1]
                row = stock.puts_formatted.iloc[idx]
                if strategy.direction =='-1':
                    #strategy.update_current("Sell","Puts",idx)
                    opt = strategy.create_option(strategy.direction,"put",row["Strike"],row["Bid"],"SP_%s"%(idx),stock.underlying)
                    strategy.add_option_to_portfolio(opt)
                    #return output_state + strategy.direction + ' %s Put for %s '%(row["Strike"],row["Bid"])

        print("Current Portfolio: ", strategy.current_portfolio)
        
        #print("Current Strat", strategy.current)

    if n_clicks and ctx.triggered and 'delete' in ctx.triggered[0]["prop_id"]:
        
        if ctx.triggered[0]["value"] > 0:
            ctx_trig = eval( ctx.triggered[0]['prop_id'].split('.')[0])
            opt_idx = ctx_trig["index"]
            print("Removing ", opt_idx)
            strategy.remove_option_from_portfolio(opt_idx)


    return update_frontend_choices()

def update_frontend_choices():
    options_text_list = []
    
    for j,i in enumerate(strategy.current_portfolio):
        options_text_list.append(html.Li(id=strategy.current_portfolio[i].option_id, className="li-port-selection",
                                        children=[strategy.option_to_text(strategy.current_portfolio[i]),
                                        html.Button(id={'type':"delete",
                                        'index':strategy.current_portfolio[i].option_id},n_clicks=0,className="opt-del-btn")]
                                                ))
    print(['delete-%s'%(i)for i in strategy.current_portfolio])
    fig = {}
    if options_text_list:
        payoff = strategy.calculate_portfolio_payoff()
        S = [p for p in range(0,int(stock.underlying*2))]
        fig = px.line(x = S,y= payoff,template="plotly_dark")
        
        """
        if abs(min(payoff)) > abs(max(payoff)):
            if payoff_count[payoff[0]] > 1:  ## If the min is displayed along horizontal line rather than bottom of slope
                fig.update_layout(xaxis=dict(range=[int(stock.underlying*0.9), int(stock.underlying*1.1)]),
                    yaxis=dict(range=[int(min(payoff)-15), int(max(payoff)+50)]))
            else:
                fig.update_layout(xaxis=dict(range=[int(stock.underlying*0.9), int(stock.underlying*1.1)]),
                        yaxis=dict(range=[int(min(payoff)*0.1), int(max(payoff)+50)]))
        else:
            fig.update_layout(xaxis=dict(range=[int(stock.underlying*0.9), int(stock.underlying*1.1)]),
                          yaxis=dict(range=[int(min(payoff)-15), int(max(payoff)*0.1)]))"""
        fig.update_layout(xaxis=dict(range=[int(stock.underlying*0.9), int(stock.underlying*1.1)]),
                          yaxis=dict(range=[-30, 30]))
        fig.update_yaxes(title_text="Profit/Loss")
        fig.update_xaxes(title_text="Underlying Price")
    return options_text_list, fig


"""@app.callback(Output('dummy-output-2', 'style'),
                    [Input('dummy-output','children')])
def make_button_callbacks(child):
    print("Change to dummy output")"""
"""
@app.callback(
    Output('dummy-output-2', 'children'),
    [Input({'type':"delete",'index':ALL}, 'n_clicks')]
)
def delete_button(*args):
    print("inside delete button")
    print("BUTTON ",args)
    ctx = dash.callback_context
    print("ctx trig: ", ctx.triggered)
    #if args[0] > 0:
    #    opt_id = args[1]
    #    strategy.remove_option_from_portfolio(opt_id)
    #    update_frontend_choices()
"""

"""
def return_choices(strategy_dict):

    res = []
    buy = strategy_dict["Buy"]
    sell = strategy_dict["Sell"]

    for c in buy["calls"]:
        row = stock.calls_formatted.iloc[c]
        res.append('+1 %s Call for %s '%(row["Strike"],row["Ask"])
    for c in buy["calls"]:
        row = stock.calls_formatted.iloc[c]
        res.append('+1 %s Call for %s '%(row["Strike"],row["Ask"])
"""


if __name__ == "__main__":
    app.run_server(debug=True)