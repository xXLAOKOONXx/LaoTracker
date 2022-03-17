from dash import Dash, html, dcc, Input, Output, State

import cassiopeia as cass
from cassiopeia.data import Queue, Position
from cassiopeia.core import Summoner, Match
import plotly.express as ex

import lao_tracker.configure_cass

app = Dash(__name__)


def get_text():
    summoners = list()
    with open('static_data/summoners', 'r') as file:
        for line in file.readlines():
            summoners.append(line.replace('\n','').replace('\r',''))

    text = ""

    for summoner_name in summoners:
        summoner = cass.get_summoner(name=summoner_name, region="EUW")

        entries: cass.LeagueSummonerEntries = summoner.league_entries

        fives: cass.LeagueEntries = entries.fives

        div = fives.division
        tier = fives.tier

        text = text + "{name} is currently {tier} {division}.\n".format(name=summoner.name,
                                                                            tier=tier,
                                                                            division=div)

    return text

def get_wards_table():
    summoner = Summoner(name='xXLAOKOONXx', region='EUW')
    match_history = cass.get_match_history(continent=summoner.region.continent,
        puuid=summoner.puuid,
        queue=Queue.ranked_solo_fives,)
    last_ten_matches = match_history[0:10]
    ward_count = []
    ward_purchased = []
    for match in last_ten_matches:
        m: Match = match
        p: cass.core.match.Participant = m.participants[summoner]
        s: cass.core.match.ParticipantStats = p.stats
        ward_count.append(s.wards_placed)
        ward_purchased.append(s.vision_wards_bought)
    data = {'Wards placed': ward_count, 'Wards purchased': ward_purchased}
    return data



app.layout = html.Div(children=[
    html.H1(children='Hello World!'),

    html.Div(children='''
        Here will be content soon...
    '''),

    html.Div(children=get_text()),

    html.Div(children='''
        Here will be even more content soon...
    '''),
    html.Button('Refresh', id='refresh-val', n_clicks=0),
    
    html.Div(id='refresh-msg'),
    dcc.Graph(id='wards-graph'),
])

@app.callback(
    Output('refresh-msg', 'children'),
    Output('wards-graph', 'figure'),
    Input('refresh-val', 'n_clicks'),
)
def refresh_data(n_clicks):
    msg = f'Clicked {n_clicks} times.'

    data = get_wards_table()

    fig = ex.line(data, labels = 'Wards placed')

    return msg, fig


server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=80)