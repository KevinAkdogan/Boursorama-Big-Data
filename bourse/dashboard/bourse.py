import dash
from dash import html, dcc
import dash.dependencies as ddep
import pandas as pd
import sqlalchemy
import plotly.graph_objs as go

DATABASE_URI = 'timescaledb://ricou:monmdp@db:5432/bourse'
engine = sqlalchemy.create_engine(DATABASE_URI)

app = dash.Dash(__name__, title="Boursorama - Dashboard", suppress_callback_exceptions=True)
server = app.server

styles = {
    'color': 'black',
    'border-radius': '20px',
}

img_style = {
    'width': '200px',
    'height': 'auto',
    'borderRadius': '20px',
    'margin': '30px'
}

ROWS_PER_PAGE = 10

app.layout = html.Div([
    html.Img(src='assets/logoboursorama.jpg', style=img_style),

    dcc.Dropdown(
        id='market-dropdown',
        options=[],
        placeholder="Select a market",
        style={'border-radius': '10px', 'border': '1px solid', 'color': 'black'}
    ),

    html.Div(id='market-actions', style={'margin-top': '20px', 'margin-bottom': '20px'}),

    html.Div(id='display-button-container'),

    html.Div(id='stock-table-container', style={'margin': 'auto', 'text-align': 'center',
                                                'width': '80%', 'padding-top': '50px'}),

    html.Div(id='display-graph-button-container', style={'margin-top': '20px', 'margin-bottom': '20px'}),

    html.Div(id='stock-graphs-container', style={'margin': 'auto', 'text-align': 'center',
                                                 'width': '80%', 'padding-top': '30px'}),

], style=styles)


@app.callback(
    ddep.Output('market-dropdown', 'options'),
    [ddep.Input('market-dropdown', 'value')]
)
def update_market_dropdown(value):
    with engine.connect() as conn:
        markets_df = pd.read_sql('SELECT * FROM markets;', conn)

    options = [{'label': f"{row['name']} - {row['alias']}", 'value': row['id']} for _, row in markets_df.iterrows()]
    return options


@app.callback(
    ddep.Output('market-actions', 'children'),
    [ddep.Input('market-dropdown', 'value')]
)
def update_market_actions(selected_market):
    if selected_market is None:
        return html.Div()

    with engine.connect() as conn:
        query = f"SELECT name, symbol FROM companies WHERE mid = {selected_market};"
        actions_df = pd.read_sql(query, conn)

    actions_dropdown = dcc.Dropdown(
        id='actions-dropdown',
        options=[{'label': f"{row['name']} - {row['symbol']}", 'value': row['symbol']} for _, row in
                 actions_df.iterrows()],
        multi=True,
        placeholder="Select companies...",
        style={'border-radius': '10px', 'border': '1px solid', 'color': 'black'}
    )

    return actions_dropdown


@app.callback(
    ddep.Output('display-button-container', 'children'),
    [ddep.Input('actions-dropdown', 'value')]
)
def display_button(selected_action):
    if selected_action:
        return html.Button('Display Table', id='display-table', n_clicks=0,
                           style={'color': 'black', 'margin': 'auto', 'display': 'block'})
    else:
        return None


@app.callback(
    ddep.Output('stock-table-container', 'children'),
    [ddep.Input('display-table', 'n_clicks')],
    [ddep.State('actions-dropdown', 'value')]
)
def display_stock_table(n_clicks, selected_actions):
    if n_clicks and selected_actions:
        all_stocks_df = pd.DataFrame()
        for selected_action in selected_actions:
            query = f"SELECT stocks.*, companies.name AS company_name, markets.name AS market_name " \
                    f"FROM stocks " \
                    f"INNER JOIN companies ON stocks.cid = companies.id " \
                    f"INNER JOIN markets ON companies.mid = markets.id " \
                    f"WHERE companies.symbol = '{selected_action}';"
            with engine.connect() as conn:
                stocks_df = pd.read_sql(query, conn)
            if not stocks_df.empty:
                all_stocks_df = pd.concat([all_stocks_df, stocks_df], ignore_index=True)

        if not all_stocks_df.empty:
            all_stocks_df['date'] = pd.to_datetime(all_stocks_df['date']).dt.strftime('%Y-%m-%d, %T.%f')

            stock_table = html.Table(
                [html.Tr([html.Th(col) for col in all_stocks_df.columns])] +
                [html.Tr([html.Td(all_stocks_df.iloc[i][col]) for col in all_stocks_df.columns]) for i in
                 range(len(all_stocks_df))]
            )

            if len(all_stocks_df) > 0:
                return html.Div([stock_table], style={'overflowY': 'scroll', 'height': '500px'})
            else:
                return html.Div("No data available.")

    return None


@app.callback(
    ddep.Output('display-graph-button-container', 'children'),
    [ddep.Input('display-table', 'n_clicks')]
)
def display_graph_button(n_clicks):
    if n_clicks:
        graph_button = html.Button('Display Graphic', id='display-graph', n_clicks=0,
                                   style={'color': 'black', 'margin': 'auto', 'display': 'block'})

        graph_parameter_dropdown = dcc.Dropdown(
            id='graph-parameter-dropdown',
            options=[
                {'label': 'Value', 'value': 'value'},
                {'label': 'Volume', 'value': 'volume'}
            ],
            value='value',
            placeholder="Select parameter for graph",
            style={'border-radius': '10px', 'border': '1px solid', 'color': 'black'},
        )

        return html.Div([graph_button, graph_parameter_dropdown], style={'margin-top': '20px'})
    else:
        return None


@app.callback(
    ddep.Output('stock-graphs-container', 'children'),
    [ddep.Input('display-graph', 'n_clicks')],
    [ddep.State('actions-dropdown', 'value'),
     ddep.State('graph-parameter-dropdown', 'value')]
)
def display_stock_graph(n_clicks, selected_actions, parameter):
    if n_clicks and selected_actions:
        price_graph = display_stock_price_graph(selected_actions, parameter)
        bollinger_graph = display_bollinger_bands_graph(selected_actions, parameter)
        return [price_graph, bollinger_graph]
    return None


def display_stock_price_graph(selected_actions, parameter):
    graphs = []
    for selected_action in selected_actions:
        query = f"SELECT * FROM stocks WHERE cid IN (SELECT id FROM companies WHERE symbol = '{selected_action}');"
        with engine.connect() as conn:
            stocks_df = pd.read_sql(query, conn)

        if not stocks_df.empty:
            stocks_df['date'] = pd.to_datetime(stocks_df['date'])
            trace = go.Scatter(x=stocks_df['date'], y=stocks_df[parameter], mode='lines+markers',
                               name=f'{selected_action} - {parameter.capitalize()}')
            graphs.append(trace)

    layout = go.Layout(title=f'Graphs for Selected Actions', xaxis=dict(title='Date'),
                       yaxis=dict(title=parameter.capitalize()), title_x=0.5)
    fig = go.Figure(data=graphs, layout=layout)

    return dcc.Graph(id='stock-price-graph', figure=fig)


def display_bollinger_bands_graph(selected_actions, parameter):
    graphs = []
    for selected_action in selected_actions:
        query = f"SELECT * FROM stocks WHERE cid IN (SELECT id FROM companies WHERE symbol = '{selected_action}');"
        with engine.connect() as conn:
            stocks_df = pd.read_sql(query, conn)

        if not stocks_df.empty:
            stocks_df['date'] = pd.to_datetime(stocks_df['date'])
            rolling_mean = stocks_df[parameter].rolling(window=20).mean()
            rolling_std = stocks_df[parameter].rolling(window=20).std()
            upper_band = rolling_mean + (rolling_std * 2)
            lower_band = rolling_mean - (rolling_std * 2)

            trace_bollinger_upper = go.Scatter(x=stocks_df['date'], y=upper_band,
                                               mode='lines', name=f'{selected_action} - Upper Bollinger Band')
            trace_bollinger_lower = go.Scatter(x=stocks_df['date'], y=lower_band,
                                               mode='lines', name=f'{selected_action} - Lower Bollinger Band')

            graphs.extend([trace_bollinger_upper, trace_bollinger_lower])

    layout = go.Layout(title=f'Bollinger Bands for Selected Actions', xaxis=dict(title='Date'),
                       yaxis=dict(title=parameter.capitalize()), title_x=0.5)
    fig = go.Figure(data=graphs, layout=layout)

    return dcc.Graph(id='bollinger-bands-graph', figure=fig)


if __name__ == '__main__':
    app.run_server(debug=True)