from dash import Dash, html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import cassiopeia as cass
from cassiopeia.data import Queue, Position
from cassiopeia.core import Summoner, Match
import plotly.express as ex
import datetime
import pandas as pd
import pickle

#import lao_tracker.configure_cass

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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
    dumb = datetime.timedelta(1)
    dumb.total_seconds()
    r = str(int(timedelta.total_seconds() / 60))+':'+str(int(timedelta.total_seconds() % 60))
    return r


app.layout = html.Div(children=[
    html.H1(children='Welcome lonely SOUL', style={'margin':'1rem'}),

    dbc.Card('Here will be more content in the future', style={'width':'fit-content', 'margin':'1rem', 'padding':'0.5rem'}),
    dbc.Button('Refresh', id='refresh-val', n_clicks=0, style={'margin':'2rem'}),
    
    html.Div(id='refresh-msg', style={'color':'white', 'margin':'1rem'}),
    dbc.Card(dash_table.DataTable(id='df-table'),
    style={'width':'50rem', 'margin':'1rem'}),
    html.Div(id='recent-match-list'),
], 
className='bg-image'
)

@app.callback(
    Output('refresh-msg', 'children'),
    Output('df-table', 'data'),
    Output('df-table', 'columns'),
    Output('recent-match-list', 'children'),
    Input('refresh-val', 'n_clicks'),
)
def refresh_data(n_clicks):


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
        'Average Tier 2 Upgrade':str(df['tier2Upgrade'].mean()),
        'Average Tier 3 Upgrade':str(df['tier3Upgrade'].mean()),

    }, index=['value'])

    table_df = table_df.transpose()

    msg = f'Last updated {str(datetime.datetime.now())}'
    table_df=table_df.reset_index()

    # recent matches
    df = df.sort_values(by='timestamp', ascending=False)
    recent_ten_games_df = df[0:10]
    childs = []
    for i, row in recent_ten_games_df.iterrows():

        tier2_color = 'danger'
        if row["tier2Upgrade"].total_seconds() < 600:
            tier2_color = 'success'
        thresh_color = 'success'
        thresh_text = 'Thresh Game'
        if not row["threshPicked"]:
            thresh_color = 'danger'
            thresh_text = 'Thresh open but not picked'
            if not row['support']:
                thresh_text = 'No Support Game'
            elif row['threshBan']:
                thresh_text = 'Thresh was banned'
                thresh_color = 'warning'
            elif row['threshPickedByOther']:
                thresh_text = 'Enemy picked Thresh'
                thresh_color = 'warning'

        c = dbc.Card(
            dbc.ListGroup(
                [
                    dbc.ListGroupItem(thresh_text, color=thresh_color, style={'width':'15rem'}),
                    dbc.ListGroupItem(f'Played at { str(row["timestamp"])}', style={'width':'20rem'}, color='dark'),
                    dbc.ListGroupItem(f'KDA: {row["kills"]}/{row["deaths"]}/{row["assists"]}', style={'width':'10rem'}),
                    dbc.ListGroupItem(f'Supportitem got wards at {tiny_timedelta(row["tier2Upgrade"])}', style={'width':'20rem'}, color=tier2_color),
                ],
                horizontal=True,
                flush=True,
                style={'width':'auto'}
            ),
            style={"margin":"1rem", 'width':'fit-content'}
        )
        childs.append(c)

    recent_match_list_children = childs

    return msg, table_df.to_dict('Records'), None, recent_match_list_children


server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=80)