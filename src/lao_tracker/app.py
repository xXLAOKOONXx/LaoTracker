from dash import Dash, html, dcc

import cassiopeia as cass

import lao_tracker.configure_cass

app = Dash(__name__)


def get_text():
    summoner = cass.get_summoner(name="xXLAOKOONXx", region="EUW")
    text = "{name} is a level {level} summoner on the {region} server.".format(name=summoner.name,
                                                                          level=summoner.level,
                                                                          region=summoner.region)
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