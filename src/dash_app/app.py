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

#import lao_tracker.configure_cass

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
lp_data_file = 'data/lp.file'

data_table_file = 'data/df.file'

def draw_df():
    df = pd.DataFrame()

    try:
        with open(data_table_file, 'rb') as f:
            df = pickle.load(f)
    except IOError:
        print("No Data Table File!")

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
        total_time = total_time + i.total_seconds()/1E3
    mean_time = int(total_time / total)
    minutes = str(int(mean_time / 60))
    if len(minutes) == 1:
        minutes = '0' + minutes
    seconds = str(int(mean_time % 60))
    if len(seconds) == 1:
        seconds = '0' + seconds
    r = minutes + ':' + seconds
    return r


app.layout = html.Div(children=[
    html.Video(id='bgVideo',src='/assets/animated-thresh.webm',
								autoPlay='autoPlay',loop='loop',muted='muted'),
    html.H1(children='Welcome lonely SOUL', style={'margin':'1rem'}),

    dbc.Card('Here will be more content in the future', style={'width':'fit-content', 'margin':'1rem', 'padding':'0.5rem'}),
    dbc.Button('Refresh', id='refresh-val', n_clicks=0, style={'margin':'2rem'}),
    
    html.Div(id='refresh-msg', style={'color':'white', 'margin':'1rem'}),
    dbc.Card(dash_table.DataTable(id='df-table'),
    style={'width':'50rem', 'margin':'1rem'}),
    dbc.Card(dcc.Graph(id='lp-graph'), class_name='lp-graph'),
    html.Div(id='recent-match-list'),
], 
className='bg-image'
)

@app.callback(
    Output('refresh-msg', 'children'),
    Output('df-table', 'data'),
    Output('df-table', 'columns'),
    Output('recent-match-list', 'children'),
    Output('lp-graph', 'figure'),
    Input('refresh-val', 'n_clicks'),
)
def refresh_data(n_clicks):

    try:
        with open(lp_data_file, 'rb') as f:
            lp_df = pickle.load(f)
    except IOError:
        print("No LP File!")

    lp_fig = go.Figure(data=[go.Scatter(x=lp_df['Timestemp'], y=lp_df['comulatedLP'], line=dict(color='#1de9b6'))], layout={
            'title': 'LP Graph'
        } )
    lp_fig.update_layout(plot_bgcolor='rgba(100,100,100,256)', paper_bgcolor='rgba(0,0,0,0)')
    lp_fig.update_xaxes(gridcolor='rgba(0,0,0,0)')
    

    recent_match_list_children = ''

    df = draw_df()

    thresh_picked = 0
    first_bloods = 0
    row_count = 0
    for _, item in df.iterrows():
        if item['threshPicked']:
            thresh_picked = thresh_picked + 1
        if item['firstbloodParticipation']:
            first_bloods = first_bloods + 1
        row_count = row_count + 1

    table_df = pd.DataFrame({
        'Average Kills': df['kills'].mean(),
        'Average Assists': df['assists'].mean(),
        'Average Deaths': df['deaths'].mean(),
        'Percentage Thresh played':thresh_picked * 100 / row_count,
        'Percentage First Bloods':first_bloods * 100 / row_count,
        'Average Tier 2 Upgrade':calculate_average(df['tier2Upgrade']),
        'Average Tier 3 Upgrade':calculate_average(df['tier3Upgrade']),

    }, index=['value'])

    table_df = table_df.transpose()

    msg = f'Last updated {str(datetime.datetime.now())}'
    table_df=table_df.reset_index()

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

    return msg, table_df.to_dict('Records'), None, recent_match_list_children, lp_fig


server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=80)