import pandas as pd
from dash import Dash, dcc, html, callback
import plotly.graph_objects as go
from dash.dependencies import Output, Input, State
import re

data = pd.read_csv("complete.csv")
app = Dash(__name__)
ALLOWED_TYPES = ("text", "number")

'''
CONTACTS
'''
contacts = pd.read_csv("contacts.csv")
for index, row in contacts.iterrows():
    temp = str(row['Phone'])
    temp = re.sub(r"[^\d+]", "", temp)
    if temp and temp[0] != "+":
        temp = "+1" + temp
    contacts.at[index, 'Phone'] = temp


def find_phone(number, contacts):
    for index, row in contacts.iterrows():
        if row['Phone'] == number:
            name = ""
            if not pd.isna(row['First name']):
                name += str(row['First name']) + " "
            if not pd.isna(row['Last name']):
                name += str(row['Last name'])
            return name
    return None


'''
DATA_ANALYSIS
'''
## Best Friend
emotion_weights = {
    'joy': 10, 'surprise': 5, 'love': 5, 'fear': -0.5, 'anger': -1, 'sadness': -1
}

friend_quality = {}
message_counts = {}

for index, row in data.iterrows():
    friend = row['Sent From']
    if friend != 'Me':
        if friend not in friend_quality.keys():
            friend_quality[friend] = {}
            for emotion in emotion_weights.keys():
                friend_quality[friend][emotion] = []
            message_counts[friend] = 0
        for emotion, weight in emotion_weights.items():
            friend_quality[friend][emotion].append(row[emotion] * weight)
        message_counts[friend] += 1

for friend in friend_quality.keys():
    for emotion in emotion_weights.keys():
        if message_counts[friend] > 0:
            friend_quality[friend][emotion] = sum(friend_quality[friend][emotion]) / message_counts[friend]
        else:
            friend_quality[friend][emotion] = 0

best_friends = sorted(friend_quality.items(), key=lambda x: sum(x[1].values()), reverse=True)
updated_best = [("0", "0") for _ in range(5)]
a, b = 0, 0
while a < 5:
    name_avail = find_phone(best_friends[b][0], contacts)
    if name_avail:
        updated_best[a] = (name_avail, round(sum(best_friends[b][1].values()), 1))
        a += 1
    b += 1

updated_worse = [("0", "0") for _ in range(5)]
i, j = 0, len(best_friends) - 1
while i < 5:
    name_avail = find_phone(best_friends[j][0], contacts)
    if name_avail:
        updated_worse[i] = (name_avail, round(sum(best_friends[j][1].values()), 1))
        i += 1
    j -= 1

## Friend Rank
for friend in friend_quality.keys():
    data.loc[data['Sent From'] == friend, 'Pos/Neg Score'] = sum(friend_quality[friend].values())
data['Rank'] = round(data['Pos/Neg Score'].rank(ascending=False), 0).fillna(0).astype(int)

## Plot
sentiment_counts = data.groupby(['sentiment']).size()
fig_pie = go.Figure(data=[go.Pie(labels=sentiment_counts.index, values=sentiment_counts)])

## Line graph
data['Time'] = pd.to_datetime(data['Time'])
message_counts = data.groupby(pd.Grouper(key='Time', freq='W'))['Time'].count().reset_index(name='Total Messages')
# Set x-axis range from the earliest to the latest message date
x_min = data['Time'].min().to_pydatetime().date()
x_max = data['Time'].max().to_pydatetime().date()
# Line graph
fig_line = go.Figure(data=go.Scatter(x=message_counts['Time'], y=message_counts['Total Messages']))
fig_line.update_layout(
    title='Total Messages Over Time',
    xaxis_title='Time',
    yaxis_title='Total Messages',
    xaxis_range=[x_min, x_max]
)

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.H1(
                                    children="Text Message Analysis",
                                    style={
                                        "color": "#ffffff",
                                        "font-size": "48px",
                                        "font-family": "Consolas, monospace",
                                        "text-align": "center",
                                    },
                                ),
                            ],
                            className="header-bar",
                            style={
                                "background-color": "#EAB2A0",
                                "padding": "10px 0",
                                "border-radius": "10px 10px 0 0",
                            },
                        ),
                        html.P(
                            children="Here's how you interacted with your friends",
                            style={
                                "color": "#ffffff",
                                "font-size": "16px",
                                "font-family": "Consolas, monospace",
                                "text-align": "center",
                                "margin-top": "10px",
                            },
                        ),
                        html.Div(
                            children=[
                                html.H2(
                                    "Your Best 'Ride or Dies'",
                                    style={
                                        "color": "#ffffff",
                                        "font-size": "24px",
                                        "font-family": "Consolas, monospace",
                                    },
                                ),
                                html.Ul(
                                    [
                                        html.Li(
                                            f"{friend} Score: {scores}",
                                            style={
                                                "color": "#ffffff",
                                                "font-size": "16px",
                                                "font-family": "Consolas, monospace",
                                            },
                                        )
                                        for friend, scores in updated_best[:5]
                                    ]
                                ),
                            ],
                            className="left-section",
                        ),
                        html.Div(
                            children=[
                                html.H2(
                                    "Here's who you could be a little nicer to!",
                                    style={
                                        "color": "#ffffff",
                                        "font-size": "24px",
                                        "font-family": "Consolas, monospace",
                                    },
                                ),
                                html.Ul(
                                    [
                                        html.Li(
                                            f"{friend} Score: {scores}",
                                            style={
                                                "color": "#ffffff",
                                                "font-size": "16px",
                                                "font-family": "Consolas, monospace",
                                            },
                                        )
                                        for friend, scores in updated_worse[:5]
                                    ]
                                ),
                            ],
                            className="left-section",
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    children=[
                                        html.H2(
                                            "Some of the words that make you the happiest",
                                            style={
                                                "color": "#ffffff",
                                                "font-size": "24px",
                                                "font-family": "Consolas, monospace",
                                            },
                                        ),
                                        html.Img(
                                            id="joy-wordcloud",
                                            src=app.get_asset_url("joy_wordcloud.png"),
                                            style={"width": "400px", "height": "300px"},
                                        ),
                                    ],
                                    style={"margin-bottom": "20px"},
                                )
                            ],
                            className="left-section",
                        ),
                        dcc.Graph(
                            id="sentiment-line-chart",
                            figure=fig_line,
                            style={"height": "400px"},
                        ),
                    ],
                    className="left-section-container",
                    style={
                        "padding": "20px",
                        "background-color": "#232323",
                        "border-radius": "0 0 10px 10px",
                    },
                ),
                html.Div(
                    children=[
                        html.H2(
                            "Sentiment Distribution",
                            style={
                                "color": "#ffffff",
                                "font-size": "24px",
                                "font-family": "Consolas, monospace",
                            },
                        ),
                        dcc.Graph(
                            id="sentiment-pie-chart",
                            figure=fig_pie,
                            style={"height": "400px"},
                        ),
                        html.H2(
                            "Search a Friend",
                            style={
                                "color": "#ffffff",
                                "font-size": "24px",
                                "font-family": "Consolas, monospace",
                            },
                        ),
                        dcc.Input(
                            id="friend_input",
                            type="text",
                            placeholder="Enter your friend's phone number (eg. +12157965565)",
                            style={
                                "width": "500px",
                                "margin-bottom": "10px",
                                "padding": "10px",
                                "font-family": "Consolas, monospace",
                                "font-size": "16px",
                            },
                        ),
                        html.Button(
                            "Search",
                            id="search-button",
                            style={
                                "background-color": "#EAB2A0",
                                "color": "#000000",
                                "padding": "10px 20px",
                                "border": "none",
                                "font-size": "16px",
                                "font-family": "Consolas, monospace",
                            },
                        ),
                        html.Div(id="search-results"),
                        dcc.Graph(
                            id="emotion-star-plot",
                            style={"height": "400px"},
                        ),
                    ],
                    className="right-section-container",
                    style={
                        "padding": "20px",
                        "background-color": "#232323",
                        "border-radius": "10px",
                    },
                ),
            ],
            className="grid-container",
            style={
                "display": "grid",
                "grid-template-columns": "1fr 1fr",
                "gap": "20px",
            },
        ),
    ],
    style={"font-family": "Consolas, monospace", "margin": "20px", "font-size": "14px"},
)

@app.callback(
    Output("search-results", "children"),
    Output("sentiment-pie-chart", "figure"),
    Output("emotion-star-plot", "figure"),
    inputs=[Input("search-button", "n_clicks")],
    state=[State("friend_input", "value")]
)
def search_friend(n_clicks, friend_input):
    if (
        n_clicks is None
        or n_clicks == 0
        or friend_input is None
        or friend_input == ""
    ):
        return html.Div(), fig_pie, go.Figure()

    friend_df = data.loc[data['Sent From'] == friend_input]
    if len(friend_df) == 0:
        return html.P("No friend found"), fig_pie, go.Figure()
    else:
        friends_name = find_phone(str(friend_input), contacts)
        if not friends_name:
            friends_name = "No contact name stored"

        # Emotion star plot graph
        fig_star_plot = go.Figure()
        for emotion in emotion_weights.keys():
            fig_star_plot.add_trace(
                go.Scatterpolar(
                    r=[friend_df[emotion].mean()],
                    theta=[emotion.capitalize()],
                    fill="toself",
                    name=emotion.capitalize(),
                )
            )
        fig_star_plot.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=False,
            title=f"Emotion Star Plot for {friends_name}",
            font=dict(color="#ffffff", size=24, family="Consolas, monospace"),
        )

        friend_score = round(sum(friend_df['Pos/Neg Score']), 1)
        friend_rank = friend_df['Rank'].iloc[0]

        return (
            html.Div(
                [
                    html.P(f"{friend_input} is saved as {friends_name}", style={"color": "#ffffff", "font-size": "16px"}),
                    html.P(f"Friend Score: {friend_score}", style={"color": "#ffffff", "font-size": "16px"}),
                    html.P(f"Friend Rank: {friend_rank}", style={"color": "#ffffff", "font-size": "16px"}),
                ]
            ),
            fig_pie,
            fig_star_plot if len(friend_df) > 0 else go.Figure(),
        )


if __name__ == "__main__":
    app.run_server()
