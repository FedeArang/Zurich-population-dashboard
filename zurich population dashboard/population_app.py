import pandas as pd
import datetime
from dash import Dash, Input, Output, dcc, html

data = (
    pd.read_csv("population_zurich.csv").assign(Date=lambda data: pd.to_datetime(data["StichtagDat"], format="%Y-%m-%d"))
    .sort_values(by="StichtagDat")
)


kreises = data["KreisLang"].unique().tolist()
age_ranges = data["AlterV20ueber80Kurz_noDM"].unique().tolist()
sex_labels = data["SexLang"].unique().tolist()
nationalities = data["HerkunftLang"].unique().tolist()
years = data["Date"].dt.year.unique().tolist()


external_stylesheets = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?"
            "family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet",
    },
]
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Analysis of Population of Zurich"

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1(
                    children="Zurich's Population Analytics", className="header-title"
                ),
                html.P(
                    children=(
                        "Analyze the behavior of trend in the population"
                        " of Zurich in different districts between 1998 and 2024"
                    ),
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="District", className="menu-title"),
                        dcc.Dropdown(
                            id="district-filter",
                            options=[
                                {"label": district, "value": district}
                                for district in kreises+["Zurich"]
                            ],
                            value="Kreis 1",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range", className="menu-title"
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=data["Date"].min().date(),
                            max_date_allowed=data["Date"].max().date(),
                            start_date=data["Date"].min().date(),
                            end_date=data["Date"].max().date(),
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="population-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="percentage_foreigners-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="percentage_men-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(
                            children="Year", className="menu-title"
                        ),
                        dcc.Dropdown(
                            id='year-picker',
                            options=[{'label': str(year), 'value': year} for year in years],
                            value=years[0],  # Set initial value to first year
                            clearable=False,
                            style={'width': '200px'}
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="pie_age-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        )
    ]
)


@app.callback(
    Output("population-chart", "figure"),
    Output("percentage_foreigners-chart", "figure"),
    Output("percentage_men-chart", "figure"),
    Output("pie_age-chart", "figure"),
    Input("district-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("year-picker", "value")
)
def update_charts(district, start_date, end_date, year):
    '''filtered_data = data.query(
        "region == @region and type == @avocado_type"
        " and Date >= @start_date and Date <= @end_date"'''
    
    if district!="Zurich":
        filtered_data = data.loc[(data['Date']>=start_date)&(data['Date']<=end_date)&(data['KreisLang']==district), ['Date', 'KreisLang', 'HerkunftCd', 'SexCd', "AlterV20ueber80Kurz_noDM", 'AnzBestWir']]
    else:
        filtered_data = data.loc[(data['Date']>=start_date)&(data['Date']<=end_date), ['Date', 'KreisLang', 'HerkunftCd', 'SexCd', "AlterV20ueber80Kurz_noDM", 'AnzBestWir']]

        
    population_chart_figure = get_figure(filtered_data, get_kreis_population, title=f"Population in {district}", color='#17B897', district=district)

    percentage_foreigners_chart_figure = get_figure(filtered_data, get_kreis_foreigners_percentage,title=f"Foreigners percentage in {district}", color="#E12D39", district=district)

    percentage_men_chart_figure = get_figure(filtered_data, get_kreis_men_percentage, title=f"Men percentage in {district}", color="#E12D40", district=district)


    pie_age_chart_figure = get_pie_age_figure(filtered_data, district, year)


    return population_chart_figure, percentage_foreigners_chart_figure, percentage_men_chart_figure, pie_age_chart_figure


def get_figure(data, fun, title, color = "#17B897", district="Zurich"):

    population_chart_figure = {
            "data": [
                {
                    "x": data["Date"].unique(),
                    "y": [fun(data, day, district) for day in data["Date"].unique().tolist()] ,
                    "type": "lines",
                    "hovertemplate": "%{y:.2f}<extra></extra>",
                },
            ],
            "layout": {
                "title": {
                    "text": title,
                    "x": 0.05,
                    "xanchor": "left",
                },
                "xaxis": {"fixedrange": False},
                "yaxis": {"fixedrange": False},
                "colorway": [color],
            },
        }
    
    return population_chart_figure


def get_pie_age_figure(data, district, year):

    date = f"{year}-01-31"
    date = pd.to_datetime(date)

    pie_chart_figure = {
    "data": [
        {
            "labels": data["AlterV20ueber80Kurz_noDM"].unique(),  # Replace with your category column
            "values": [get_kreis_age(data, age, district, date) for age in data["AlterV20ueber80Kurz_noDM"].unique().tolist()],  # Replace with your values
            "type": "pie",
            "hole": 0.4,  # Set to 0 for regular pie chart, > 0 for donut chart
            "hoverinfo": "label+percent",
            "textinfo": "value+percent",
            #"marker": {
                #"colors": ["#E12D40", "#2D40E1", "#40E12D", "#E1D40E", "#40E1D4"],  # Custom colors for each slice
            #},
        }
    ],
    "layout": {
        "title": {
            "text": f"Age Distribution in {district} in {year}",
            "x": 0.5,  # Center the title
            "xanchor": "center"
        },
        "showlegend": True,
        "legend": {
            "orientation": "h",  # Horizontal legend
            "yanchor": "bottom",
            "y": -0.2,  # Position below chart
            "xanchor": "center",
            "x": 0.5
        }
    }
}
    
    return pie_chart_figure


def get_kreis_population(data, day, kreis):

    return sum(data.loc[(data['Date']==day) & (data['KreisLang']==kreis), 'AnzBestWir']) if kreis!="Zurich" else sum(data.loc[data['Date']==day, 'AnzBestWir'])

def get_kreis_age(data, age, kreis, date):

    return sum(data.loc[(data['Date']==date) & (data['KreisLang']==kreis) & (data['AlterV20ueber80Kurz_noDM']==age), 'AnzBestWir']) if kreis!="Zurich" else sum(data.loc[(data['Date']==date) & (data['AlterV20ueber80Kurz_noDM']==age), 'AnzBestWir'])

def get_kreis_foreigners_percentage(data, day, kreis):

    if kreis !="Zurich":
        swiss = sum(data.loc[(data['Date']==day) & (data['KreisLang']==kreis) & (data['HerkunftCd']==1), 'AnzBestWir'])
        foreigners = sum(data.loc[(data['Date']==day) & (data['KreisLang']==kreis) & (data['HerkunftCd']==2), 'AnzBestWir'])
    else:
        swiss = sum(data.loc[(data['Date']==day) & (data['HerkunftCd']==1), 'AnzBestWir'])
        foreigners = sum(data.loc[(data['Date']==day) & (data['HerkunftCd']==2), 'AnzBestWir'])

    return foreigners/(swiss+foreigners)

def get_kreis_men_percentage(data, day, kreis):

    if kreis!="Zurich":
        men = sum(data.loc[(data['Date']==day) & (data['KreisLang']==kreis) & (data['SexCd']==1), 'AnzBestWir'])
        women = sum(data.loc[(data['Date']==day) & (data['KreisLang']==kreis) & (data['SexCd']==2), 'AnzBestWir'])
    else:
        men = sum(data.loc[(data['Date']==day) & (data['SexCd']==1), 'AnzBestWir'])
        women = sum(data.loc[(data['Date']==day) & (data['SexCd']==2), 'AnzBestWir'])
    return men/(men+women)


if __name__ == "__main__":
    app.run_server(debug=True)
