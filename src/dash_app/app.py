from dash import Dash, html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import cassiopeia as cass
from cassiopeia.data import Queue, Position
from cassiopeia.core import Summoner, Match
import plotly.express as ex
import datetime
import pandas as pd
import pickle
import plotly.graph_objs as go
import logging

#import lao_tracker.configure_cass

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
lp_data_file = 'data/lp.file'

data_table_file = 'data/df.file'
season_12_start = datetime.datetime(2022,1,7)

def draw_df():
    df = pd.DataFrame()

    try:
        with open(data_table_file, 'rb') as f:
            df = pickle.load(f)
    except IOError:
        logging.warning("No Data Table File!")

    return df

def tiny_timedelta(timedelta):
    minutes = str(int(timedelta.total_seconds() / 60))
    if len(minutes) == 1:
        minutes = '0' + minutes
    seconds = str(int(timedelta.total_seconds() % 60))
    if len(seconds) == 1:
        seconds = '0' + seconds
    r = minutes + ':' + seconds
    return r

def two_space(input):
    input = str(input)
    if len(input) == 2:
        return input
    if len(input) == 1:
        return ' ' + input    
    return input

def calculate_average(enumerable_timedeltas):
    total = 0
    total_time = 0
    for _, i in enumerate(enumerable_timedeltas):
        total = total + 1
        total_time = total_time + i.total_seconds()
    mean_time = int(total_time / total)
    minutes = str(int(mean_time / 60))
    if len(minutes) == 1:
        minutes = '0' + minutes
    seconds = str(int(mean_time % 60))
    if len(seconds) == 1:
        seconds = '0' + seconds
    r = minutes + ':' + seconds
    return r

def get_card(label, value):
    margin = '3px'
    c = dbc.Card(
        dbc.ListGroup(
            [
                dbc.ListGroupItem(label, class_name='standard-item', style={'width':'20rem'}),
                dbc.ListGroupItem('', class_name='standard-item', style={'width':margin, 'padding':'0px', 'backgroundColor':'#00000000'}),
                dbc.ListGroupItem(value, class_name='standard-item', style={'width':'10rem', 'text-align':'right'}),
            ],
            horizontal=True,
            flush=True,
            style={'width':'auto'}
        ),
        style={'margin-left': '1rem', 'margin-top':margin, 'width':'fit-content', 'backgroundColor':'#00000000'}
    )
    return c

app.title = 'LaoTracker'

app.layout = html.Div(children=[
    html.Video(id='bgVideo',src='/assets/animated-thresh.webm',
								autoPlay='autoPlay',loop='loop',muted='muted'),
    html.H1(children='Welcome lonely SOUL', style={'margin':'1rem'}),

    dbc.Button('Refresh page', id='refresh-val', n_clicks=0, style={'margin':'2rem'}),
    html.Div(id='df-table-cards'),
    html.Div(id='recent-match-list'),
    dbc.Card(dcc.Graph(id='lp-graph'), class_name='lp-graph'),
    dbc.Card(dcc.Graph(id='lp-graph-games'), class_name='lp-graph'),
], 
className='bg-image'
)

@app.callback(
    Output('recent-match-list', 'children'),
    Output('lp-graph', 'figure'),
    Output('lp-graph-games', 'figure'),
    Output('df-table-cards', 'children'),
    Input('refresh-val', 'n_clicks'),
)
def refresh_data(n_clicks):

    try:
        with open(lp_data_file, 'rb') as f:
            lp_df = pickle.load(f)
    except IOError:
        logging.warning("No LP File!")


    r_df = lp_df[~lp_df['recentGame'].isnull()]
    registered_game_ids = []
    rows = []
    for _, row in r_df.iterrows():
        if row['recentGame'] not in registered_game_ids:
            registered_game_ids.append(row['recentGame'])
            rows.append(row)
            
    newest_df = pd.DataFrame(rows)
    newest_df = newest_df.sort_values(by='Timestemp', ascending=True)
    x_arr = [i for i in range(len(newest_df))]

    lp_fig_games = go.Figure(data=[go.Scatter(x=x_arr, y=newest_df['comulatedLP'], line=dict(color='#1de9b6'))], layout={
            'title': 'LP Graph (Games)'
        } )
    lp_fig_games.update_layout(plot_bgcolor='rgba(100,100,100,256)', paper_bgcolor='rgba(0,0,0,0)')
    lp_fig_games.update_xaxes(gridcolor='rgba(0,0,0,0)')

    lp_fig = go.Figure(data=[go.Scatter(x=lp_df['Timestemp'], y=lp_df['comulatedLP'], line=dict(color='#1de9b6'))], layout={
            'title': 'LP Graph'
        } )
    lp_fig.update_layout(plot_bgcolor='rgba(100,100,100,256)', paper_bgcolor='rgba(0,0,0,0)')
    lp_fig.update_xaxes(gridcolor='rgba(0,0,0,0)')
    

    recent_match_list_children = ''

    df = draw_df()

    df = df[df.timestamp > season_12_start]

    thresh_picked = 0
    first_bloods = 0
    row_count = 0
    for _, item in df.iterrows():
        if item['threshPicked']:
            thresh_picked = thresh_picked + 1
        if item['firstbloodParticipation']:
            first_bloods = first_bloods + 1
        row_count = row_count + 1
        
    table_df_view = []
    table_df_view.append(get_card('Average Kills', '%.2f' % round(df['kills'].mean(),2)))
    table_df_view.append(get_card('Average Deaths', '%.2f' % round(df['deaths'].mean(),2)))
    table_df_view.append(get_card('Average Assists', '%.2f' % round(df['assists'].mean(),2)))
    table_df_view.append(get_card('Percentage Thresh played', '%.2f' % round(thresh_picked * 100 / row_count, 2) + ' %'))
    table_df_view.append(get_card('Percentage First Bloods', '%.2f' % round(first_bloods * 100 / row_count, 2) + ' %'))
    table_df_view.append(get_card('Average Tier 2 Upgrade on Thresh', calculate_average(df[df.threshPicked]['tier2Upgrade'])))
    table_df_view.append(get_card('Average Tier 3 Upgrade on Thresh', calculate_average(df[df.threshPicked]['tier3Upgrade'])))

    # recent matches
    df = df.sort_values(by='timestamp', ascending=False)
    recent_ten_games_df = df[0:10]
    childs = []
    for i, row in recent_ten_games_df.iterrows():

        tier2_class = 'goal-failed'
        if row["tier2Upgrade"].total_seconds() < 600:
            tier2_class = 'goal-met'
        thresh_class = 'goal-met'
        thresh_text = 'Thresh Game'
        if not row["threshPicked"]:
            thresh_class = 'goal-failed'
            thresh_text = 'Thresh not picked'
            if not row['support']:
                thresh_text = 'No Support Game'
            elif row['threshBan']:
                thresh_text = 'Thresh was banned'
                thresh_class = 'goal-almost-met'
            elif row['threshPickedByOther']:
                thresh_text = 'Enemy picked Thresh'
                thresh_class = 'goal-almost-met'

        win_text = 'WIN'
        win_class = 'goal-met'
        if not row['win']:
            win_text = 'LOOSE'
            win_class = 'goal-failed'

        red_trinket_text = f'Update to Red Trinket: {tiny_timedelta(row["redTrinketPurchase"])}'
        red_trinket_class = 'goal-met'
        if row['redTrinketPurchase'].total_seconds() > row["tier2Upgrade"].total_seconds() + 60:
            red_trinket_class = 'goal-almost-met'
        if row['redTrinketPurchase'].total_seconds() > row["tier2Upgrade"].total_seconds() + 120:
            red_trinket_class = 'goal-failed'

        kda_class = 'goal-met'
        if row["deaths"] > 4:
            kda_class = 'goal-almost-met'
        if row["deaths"] > 6:
            kda_class = 'goal-failed'


        c = dbc.Card(
            dbc.ListGroup(
                [
                    dbc.ListGroupItem(win_text, class_name=win_class, style={'width':'5rem'}),
                    dbc.ListGroupItem(thresh_text, class_name=thresh_class, style={'width':'11rem'}),
                    dbc.ListGroupItem(f'Played at { str(row["timestamp"])}', style={'width':'16rem'}, class_name='standard-item'),
                    dbc.ListGroupItem(f'KDA: {two_space(row["kills"])}/{two_space(row["deaths"])}/{two_space(row["assists"])}', style={'width':'10rem'}, class_name=kda_class),
                    dbc.ListGroupItem(f'Supportitem got wards at {tiny_timedelta(row["tier2Upgrade"])}', style={'width':'16rem'}, class_name=tier2_class),
                    dbc.ListGroupItem(red_trinket_text, style={'width':'15rem'}, class_name=red_trinket_class),
                    dbc.ListGroupItem(f'Gameduration: {tiny_timedelta(row["gametime"])}', style={'width':'12rem'}, class_name='standard-item'),
                ],
                horizontal=True,
                flush=True,
                style={'width':'auto'}
            ),
            style={"margin":"1rem", 'width':'fit-content'}
        )
        childs.append(c)

    recent_match_list_children = childs

    return recent_match_list_children, lp_fig, lp_fig_games, table_df_view


server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=80)