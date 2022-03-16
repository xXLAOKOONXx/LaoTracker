from dash import Dash, html, dcc

import cassiopeia as cass
from cassiopeia.data import Queue, Position
from cassiopeia.core import Summoner

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

app.layout = html.Div(children=[
    html.H1(children='Hello World!'),

    html.Div(children='''
        Here will be content soon...
    '''),

    html.Div(children=get_text()),

    html.Div(children='''
        Here will be even more content soon...
    '''),
])

server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=80)