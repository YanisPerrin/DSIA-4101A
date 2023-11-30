from re import template
import pandas as pd
import pycountry_convert as pc
import numpy as np
import plotly_express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import html, dcc, Input, Output, dash, State

######################################################################################################################################################################################

#Traitement des données

# On scrappe les données sur internet à l'aide de la méthode pd.read_html() qui permet de récupérer les tableaux disponibles sur un site web
def recup_data_decennie(url, year):
    name= pd.read_html(url)[1]
    name= name.assign(Year=year)
    name['Rank']=[i for i in range(1,len(name)+1)]
    name = name[['Country', 'Cost of Living Index', 'Year', 'Rank']]
    return name

#On traite les données pour l'année 2022, ce tableau est différent des données récupérés précédemment car il ne contient pas l'indice du coût de la vie 
#mais le coût de la vie en dollar(ex: France -> 1363$), ce qui nous paraît être des données plus parlantes pour construire un histogramme
#On utilise pycountry_convert qui possède les méthodes pc.country_name_to_country_alpha2() et pc.country_alpha2_to_continent_code()
#pc.country_name_to_country_alpha2() nous permet de convertir un nom de pays aux valeurs ISO 3166-1 alpha-2 associé à chaque pays
#pc.country_alpha2_to_continent_code() nous permet de convertir les valeurs ISO 3166-1 alpha-2 de chaque pays aux nom des continents réduit en deux lettres (ex: Europe -> EU)
#Cependant, certains pays ne sont pas reconnus par l'algorithme comme le Vatican, Timor Oriental ou Kosovo, 
#On supprime donc ces valeurs de la dataframe, on applique le filtre puis on remet les valeurs en ajoutant le nom du continent manuellement.
def data_processing_2022(url):
    df = pd.read_html(url)[0]
    df1 = pd.DataFrame(data=df)
    df1['Cost of living']=[df1['Cost of living'][i].replace(df1['Cost of living'][i][0],'') for i in range(0,len(df1['Cost of living']))]
    df1['Cost of living'] = df1['Cost of living'].astype(int)
    df1=df1.replace(to_replace=["DR Congo","Saint Vincent", "Vatican","Curacao"], value=["Congo, The Democratic Republic of the","Saint Vincent and the Grenadines","Holy See (Vatican City State)","Curaçao"])
    f = lambda x: pc.country_name_to_country_alpha2(x, cn_name_format="default")
    f1 = lambda x: pc.country_alpha2_to_continent_code(x)
    df1['Iso Code 2'] = df1['Country'].apply(f)
    df2=df1[df1['Iso Code 2']!='VA']
    df3=df2[df2['Iso Code 2']!='TL']
    df1['Continent'] = df3['Iso Code 2'].apply(f1)
    df1['Continent'] = df1['Continent'].replace(to_replace=["EU", "AS", "SA", "AF", "NA", "OC"], value=["Europe", "Asia", "South America", "Africa", "North America", "Oceania"])
    df1.loc[104,"Continent"]='Europe'
    df1.loc[176,"Continent"]='Asia'
    return df1

#On traite ici les données qui contiennent l'indice du coût de la vie. Même démarche que précédemment.
def data_processing_decennie(table):
    table1=table[table['Country']!=('Kosovo (Disputed Territory)')]
    table1=table1.replace(to_replace=["Bosnia And Herzegovina","Trinidad And Tobago"], value=["Bosnia and Herzegovina","Trinidad and Tobago"])
    f = lambda x: pc.country_name_to_country_alpha2(x, cn_name_format="default")
    f1 = lambda x: pc.country_alpha2_to_continent_code(x)
    f2 = lambda x: pc.country_name_to_country_alpha3(x, cn_name_format="default")   
    table1['Iso Code 2'] = table1['Country'].apply(f)
    table1['Continent'] = table1['Iso Code 2'].apply(f1)
    table1['Iso Code 3'] = table1['Country'].apply(f2)
    table1['Continent'] = table1['Continent'].replace(to_replace=["EU", "AS", "SA", "AF", "NA", "OC"], value=["Europe", "Asia", "South America", "Africa", "North America", "Oceania"])
    kosovo=table[table['Country'].str.contains('Kosovo')]
    kosovo=kosovo.assign(Continent="Europe")
    kosovo["Iso Code 2"]=['XK','XK','XK']
    kosovo["Iso Code 3"]=['XXK','XXK','XXK']
    table_final=[table1,kosovo]
    cost_of_living= pd.concat(table_final)
    cost_of_living=cost_of_living.sort_values(['Country', 'Year'], ignore_index=True)
    return cost_of_living


#On applique les fonctions crées précédemment pour traiter les données.    
table_2010=recup_data_decennie("https://www.numbeo.com/cost-of-living/rankings_by_country.jsp?title=2010", "2010")
table_2012=recup_data_decennie("https://www.numbeo.com/cost-of-living/rankings_by_country.jsp?title=2012", "2012")
table_2014=recup_data_decennie("https://www.numbeo.com/cost-of-living/rankings_by_country.jsp?title=2014", "2014")
table_2016=recup_data_decennie("https://www.numbeo.com/cost-of-living/rankings_by_country.jsp?title=2016", "2016")
table_2018=recup_data_decennie("https://www.numbeo.com/cost-of-living/rankings_by_country.jsp?title=2018", "2018")
table_2020=recup_data_decennie("https://www.numbeo.com/cost-of-living/rankings_by_country.jsp?title=2020", "2020")
table_2022=recup_data_decennie("https://www.numbeo.com/cost-of-living/rankings_by_country.jsp?title=2022", "2022")
table_total=[table_2010,table_2012,table_2014,table_2016,table_2018,table_2020,table_2022]
result = pd.concat(table_total)
cost_of_living_decennie=data_processing_decennie(result)
cost_of_living_2022=data_processing_2022('https://livingcost.org/cost')

cost_of_living_decennie.to_csv("cost_of_living_decennie.csv") 
cost_of_living_2022.to_csv("cost_of_living_2022.csv")
#optionelle ici car les données sont récupérés dynamiquement mais sera utilisé pour l'unité R et DataVisualization.

######################################################################################################################################################################################

#Visualisation des données

#Création de la carte avec interface dynamique
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

year=2010
cost_of_living_decennie=pd.read_csv("cost_of_living_decennie.csv")
cost_of_living_decennie['Year']= cost_of_living_decennie['Year'].astype('int')
cost=cost_of_living_decennie.sort_values(['Year'])
years=list(set(cost['Year'].unique()))
data={year:cost_of_living_decennie.query("Year == @year") for year in years}

title_map={
    2010 : 'Cost of Living Index by country in 2010',
    2012 : 'Cost of Living Index by country in 2012',
    2014 : 'Cost of Living Index by country in 2014',
    2016 : 'Cost of Living Index by country in 2016',
    2018 : 'Cost of Living Index by country in 2018',
    2020 : 'Cost of Living Index by country in 2020',
    2022 : 'Cost of Living Index by country in 2022'
}
#On crée cette carte à l'aide de go.choropleth qui permet de créer une carte choropleth, cette carte s'actualisera en fonction de l'année entrée en paramètre.
figmap = go.Figure(data=go.Choropleth(
    locations = data[year]['Iso Code 3'],
    z = data[year]['Cost of Living Index'],
    text = data[year]['Country'],
    #colorscale = 'Blues',
    #colorscale= [ '#1a9641', '#a6d96a', '#ffffbf', '#fdae61', '#d7191c'],
    #colorscale="RdBu",
    colorscale= ['#ffffbf', '#fdae61', '#d7191c'],
    autocolorscale=False,
    reversescale=False,
    marker_line_color='darkgrey',
    marker_line_width=0.5,
    colorbar=dict(
        borderwidth=1,
        titlefont=dict(
                size=14,
                family='Times New Roman'),
        x=0.8,
        y=0.45),
        colorbar_title = 'Cost of living Index',
    
))
figmap.update_geos(
    projection_type="orthographic",
    landcolor="white",
    oceancolor="LightBlue",
    showocean=True,
    lakecolor="LightBlue"
)
figmap.update_layout(
        height=700,
        template="simple_white",
        title={
        'text': title_map[year],
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
        font=dict(
        family="Courier New, monospace",
        size=18,
        color="RebeccaPurple"
    ), 
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='equirectangular'
    ),
        annotations = [dict(
                x=0.50,
                y=-0.1,
                xref='paper',
                yref='paper',
                text='Source:<a href="https://www.numbeo.com/cost-of-living/rankings_by_country.jsp">\
                    Numbeo.com</a>',
                showarrow = False
            )],)

#Création de l'histogramme
#On aura besoin de données associées à chaque continent pour construire les différentes figures qui composeront ce dashboard.
#df sera plus simple à utiliser
df_2022=cost_of_living_2022 
asia=df_2022.query("Continent=='Asia'")
africa=df_2022.query("Continent=='Africa'")
europe=df_2022.query("Continent=='Europe'")
oceania=df_2022.query("Continent=='Oceania'")
north_america=df_2022.query("Continent=='North America'")
south_america=df_2022.query("Continent=='South America'")
country_g8=df_2022.query("Country==['Germany', 'Canada', 'United States', 'France', 'United Kingdom', 'Italy', 'Japan', 'Russia']")
    
figc = go.Figure()
figc.add_trace(go.Histogram(
        x=asia['Cost of living'],
        text="Asia",
        hovertemplate=
            "<b>Asia</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Number of Countries :%{y}<br>" +
            "<extra></extra>",
        name='Asia', # name used in legend and hover labels
        marker_color='Orange',
))
figc.add_trace(go.Histogram(
        x=europe['Cost of living'],
        text="Europe",
        hovertemplate=
            "<b>Europe</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Number of Countries :%{y}<br>" +
            "<extra></extra>",
        name='Europe', # name used in legend and hover labels
        marker_color='Blue',
))
figc.add_trace(go.Histogram(
        x=north_america['Cost of living'],
        text="North America",
        hovertemplate=
            "<b>North America</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Number of Countries :%{y}<br>" +
            "<extra></extra>",
        name='North America', # name used in legend and hover labels
        marker_color='Red',

))
figc.add_trace(go.Histogram(
        x=south_america['Cost of living'],
        text="South America",
        hovertemplate=
            "<b>South America</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Number of Countries :%{y}<br>" +
            "<extra></extra>",
        name='South America', # name used in legend and hover labels
        marker_color='Yellow',
 
))
figc.add_trace(go.Histogram(
        x=africa['Cost of living'],
        text="Africa",
        hovertemplate=
            "<b>Africa</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Number of Countries :%{y}<br>" +
            "<extra></extra>",
        name='Africa', # name used in legend and hover labels
        marker_color="Green",
))
figc.add_trace(go.Histogram(
        x=oceania['Cost of living'],
        text="Oceania",
        hovertemplate=
            "<b>Oceania</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Number of Countries :%{y}<br>" +
            "<extra></extra>",
        name='Oceania', # name used in legend and hover labels
        marker_color="Grey",
))
figc.update_layout(
        height=500,
        barmode="stack",
        title_text='Number of countries by continent according to the cost of living in 2022', # title of plot
        xaxis_title_text='Cost of living ($)', # xaxis label
        yaxis_title_text='Number', # yaxis label
        #bargap=0.2, gap between bars of adjacent location coordinates
        #bargroupgap=0.1 # gap between bars of the same location coordinates
)

#Création des bargraph
fighp = go.Figure()
fighp.add_trace(go.Histogram(
        x=asia['Cost of living'],
        histnorm='probability',
        text="Asia",
        hovertemplate=
            "<b>Asia</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Probability :%{y:.1%}<br>" +
            "<extra></extra>",
        name='Asia', # name used in legend and hover labels
        #marker_color='salmon',
        
))
fighp.add_trace(go.Histogram(
        x=europe['Cost of living'],
        histnorm='probability',
        text="Europe",
        hovertemplate=
            "<b>Europe</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Probability :%{y:.1%}<br>" +
            "<extra></extra>",
        name='Europe', # name used in legend and hover labels
        #marker_color='royalblue',
        
))
fighp.add_trace(go.Histogram(
        x=north_america['Cost of living'],
        histnorm='probability',
        text="North America",
        hovertemplate=
            "<b>North America</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Probability :%{y:.1%}<br>" +
            "<extra></extra>",
        name='North America', # name used in legend and hover labels
        #marker_color='red',
        
))
fighp.add_trace(go.Histogram(
        x=south_america['Cost of living'],
        histnorm='probability',
        text="South America",
        hovertemplate=
            "<b>South America</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Probability :%{y:.1%}<br>" +
            "<extra></extra>",
        name='South America', # name used in legend and hover labels
        #marker_color='violet',
        
))
fighp.add_trace(go.Histogram(
        x=africa['Cost of living'],
        histnorm='probability',
        text="Africa",
        hovertemplate=
            "<b>Africa</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Probability :%{y:.1%}<br>" +
            "<extra></extra>",
        name='Africa', # name used in legend and hover labels
        #marker_color="mediumseagreen",
        
))
fighp.add_trace(go.Histogram(
        x=oceania['Cost of living'],
        histnorm='probability',
        text="Oceania",
        hovertemplate=
            "<b>Oceania</b><br><br>" +
            "Cost of living :%{x:$,.0f}(+/- 100$)<br>" +
            "Probability :%{y:.1%}<br>" +
            "<extra></extra>",
        name='Oceania', # name used in legend and hover labels
        #marker_color="aquamarine",
        opacity=0.75
))
fighp.update_layout(
        height=500,
        title_text='Probability of cost of living for each continent in 2022', 
        xaxis_title_text='Cost of living ($)', # xaxis label
        yaxis_title_text='Probability', # yaxis label
        bargap=0.2, # gap between bars of adjacent location coordinates
        #bargroupgap=0.1 # gap between bars of the same location coordinates
)


#Création du bar graph avec boutons plotly
    
mean_asia=asia['Cost of living'].mean()
mean_africa=africa['Cost of living'].mean()
mean_europe=europe['Cost of living'].mean()
mean_oceania=oceania['Cost of living'].mean()
mean_na=north_america['Cost of living'].mean()
mean_sa=south_america['Cost of living'].mean()

mean_continent=pd.DataFrame()
mean_continent=mean_continent.assign(Continent=["South America","Africa","Europe","Asia","North America","Oceania"])
mean_continent=mean_continent.assign(Mean=[mean_sa,mean_africa,mean_europe,mean_asia,mean_na,mean_oceania])
mean_continent=mean_continent.sort_values(['Mean'], ascending=False)

figbar = make_subplots()
'''fig.add_trace(
    go.Bar(x=country_g8['Country'],y=country_g8['Cost of living'], marker=dict(color="crimson"), showlegend=False),
    row=1, col=1
)'''
figbar.add_trace(
    go.Bar(x=df_2022['Country'],y=df_2022['Cost of living'], marker=dict(color="crimson"), showlegend=False, text=df_2022['Country'],
    hovertemplate=
        "<b>%{text}</b><br><br>" +
        "Cost of living : %{y}<br>" +
        "<extra></extra>",),
    
    
)
figbar.update_layout(
    height=600,
    template="simple_white",
    title="Cost of Living ($) by country in 2022",
    xaxis=dict(title_text="Country"),
    yaxis=dict(title_text="Cost of living ($)"),
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            x=0.7,
            y=1.2,
            showactive=True,
            buttons=list(
                [
                    dict(
                        label="General",
                        method="update",
                        args=[{"y": [df_2022['Cost of living']], "x": [df_2022["Country"]], "marker":dict(color="crimson"),"text" : [df_2022['Country']]},
                        {'title': 'Cost of Living ($) by country in 2022'}]
                        
                        
                        
                    ),
                    dict(
                        label="Asia",
                        method="update",
                        args=[{"y": [asia['Cost of living']], "x": [asia["Country"]],"marker":dict(color="Orange"),"text" : [asia['Country']]},
                        {'title': 'Cost of Living ($) by country in Asia (2022)'}]
                        
                        
                    ),
                    dict(
                        label="Europe",
                        method="update",
                        args=[{"y": [europe['Cost of living']], "x": [europe["Country"]], "marker":dict(color="Blue"),"text" : [europe['Country']]},
                        {'title': 'Cost of Living ($) by country in Europe (2022)'}]
                    ),
                    dict(
                        label="Africa",
                        method="update",
                        args=[{"y": [africa['Cost of living']], "x": [africa["Country"]], "marker":dict(color="Green"),"text" : [africa['Country']]},
                        {'title': 'Cost of Living ($) by country in Africa (2022)'}]
                    ),
                    dict(
                        label="North America",
                        method="update",
                        args=[{"y": [north_america['Cost of living']], "x": [north_america["Country"]], "marker":dict(color="Muted Blue"),"text" : [north_america['Country']]},
                        {'title': 'Cost of Living ($) by country in North America (2022)'}]
                    ),
                    dict(
                        label="South America",
                        method="update",
                        args=[{"y": [south_america['Cost of living']], "x": [south_america["Country"]], "marker":dict(color="Yellow"),"text" : [south_america['Country']]},
                        {'title': 'Cost of Living ($) by country in South America (2022)'}]
                    ),
                    dict(
                        label="Oceania",
                        method="update",
                        args=[{"y": [oceania['Cost of living']], "x": [oceania["Country"]], "marker":dict(color="Grey"),"text" : [oceania['Country']]},
                        {'title': 'Cost of Living ($) by country in Oceania (2022)'}]
                    ),
                    dict(
                        label="Mean Continent",
                        method="update",
                        args=[{"y": [mean_continent['Mean']], "x": [mean_continent["Continent"]], "marker":dict(color="Pink"),"text" : [mean_continent['Continent']]},
                        {'title': 'Mean of the cost of living($) by Continent in 2022'}]
                    ),
                    dict(
                        label="G8 Countries",
                        method="update",
                        args=[{"y": [country_g8['Cost of living']], "x": [country_g8["Country"]], "marker":dict(color="Black"),"text" : [country_g8['Country']]},
                        {'title': 'Cost of Living ($) by G8 countries in 2022'}]
                    ),
                ]
            ),
        )
    ]
)

#Graphique circulaire
top_20_cost_of_living = cost_of_living_2022[0:20]
top_20_cost_of_living = top_20_cost_of_living.assign(Count=1)
last_20_cost_of_living = cost_of_living_2022[-20:]
last_20_cost_of_living = last_20_cost_of_living.assign(Count=1)
specs = [[{'type':'domain'}, {'type':'domain'}]]
figpie = make_subplots(rows=1, cols=2, specs=specs,subplot_titles=['Among the 20 countries with the highest cost of living in 2022', 'Among the 20 countries with the lowest cost of living in 2022'])
figpie.add_trace(go.Pie(labels=top_20_cost_of_living['Continent'], values=top_20_cost_of_living['Count'], name='Continent', 
                     ), 1, 1)
figpie.add_trace(go.Pie(labels=last_20_cost_of_living['Continent'], values=last_20_cost_of_living['Count'], name='Continent',
                     ), 1, 2)
figpie.update_traces(hoverinfo='label+value+percent+name')
figpie.update_layout(height=500,
            title={
            'text': "Percentage of Continents",
            'y':0.95,
            'x':0.50,
            },
            font=dict(
            family="Courier New, monospace",
            size=18,
            color="RebeccaPurple"
            ), 
)
figpie = go.Figure(figpie)

#Dash
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(children=[
                            html.H1(
                            children='Map',
                            style={'textAlign': 'center','color': 'black','border':'thick double #32a1ce'}
                            ),
                            dcc.Interval(id='interval', disabled=True),
                            dcc.Graph(
                                id='graph1',
                                figure=figmap
                            ),
                            html.Label('Year'),
                            dcc.Slider(
                                min=cost_of_living_decennie['Year'].min(),
                                max=cost_of_living_decennie['Year'].max(),
                                step=None,
                                value=2010,
                                marks={str(year): str(year) for year in years},
                                id="year-slider",  
                            ),
                            html.Button("Play/Pause", id="play"),
                            html.Div(children=f'*This map show the cost of living index for each country by year around the world. You can choose the year for which you want to see the map.',
                                style={'textAlign': 'center', 'color': '#8FBC8F','font-size':18}
                            ),


                            html.H1(
                            children='Histogram',
                            style={'textAlign': 'center','color': 'black','border':'thick double #32a1ce'}
                            ),
                            dcc.Graph(
                                id='graph2',
                                figure=figc
                            ),
                            html.Div(children=f'*This histogram shows the number of countries per continent for a certain cost of living.',
                                style={'textAlign': 'center', 'color': '#8FBC8F','font-size':18}
                            ),


                            html.H1(
                            children='Bargraph',
                            style={'textAlign': 'center','color': 'black','border':'thick double #32a1ce'}
                            ),
                            dcc.Graph(
                                id='graph3',
                                figure=figbar
                            ), 
                            html.Div(children=f'*This bargraph show the cost of living for each country in 2022 around the world. You can also sort it by continent or G8 countries.',
                                style={'textAlign': 'center', 'color': '#8FBC8F','font-size':18}
                            ),
                            dcc.Graph(
                                id='graph4',
                                figure=fighp
                            ),
                            html.Div(children=f'*This histogram shows the probability of the cost of living for each continent.',
                                style={'textAlign': 'center', 'color': '#8FBC8F','font-size':18}
                            ),


                            html.H1(
                            children='Pies',
                            style={'textAlign': 'center','color': 'black','border':'thick double #32a1ce'}
                            ), 
                            dcc.Graph(
                                id='graph5',
                                figure=figpie
                            ), 
                            html.Div(children=f'*This pie show the percentage of continents among the 20 countries with the highest/lowest cost of living in 2022.',
                                style={'textAlign': 'center', 'color': '#8FBC8F','font-size':18}

                            ), 

        ]
        )
@app.callback(
    Output("graph1", "figure"),
    Output("year-slider", "value"),
    Input("interval", "n_intervals"),
    State("year-slider", "value"),
    prevent_initial_call=True,
)
def update_figure(n,input_value): 
    index = years.index(input_value)
    index = (index + 1) % len(years)
    year = years[index]

    figmap= go.Figure(data=go.Choropleth(
    locations = data[year]['Iso Code 3'],
    z = data[year]['Cost of Living Index'],
    text = data[year]['Country'],
    colorscale= ['#ffffbf', '#fdae61', '#d7191c'],
    autocolorscale=False,
    reversescale=False,
    marker_line_color='darkgrey',
    marker_line_width=0.5,
    colorbar=dict(
        borderwidth=1,
        titlefont=dict(
                size=14,
                family='Times New Roman'),
        x=0.8,
        y=0.45),
        colorbar_title = 'Cost of living Index',
    ))
    figmap.update_geos(
    projection_type="orthographic",
    landcolor="white",
    oceancolor="LightBlue",
    showocean=True,
    lakecolor="LightBlue"
)
    figmap.update_layout(
        height=700,
        template="simple_white",
        title={
        'text': title_map[year],
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
        font=dict(
        family="Courier New, monospace",
        size=18,
        color="RebeccaPurple"
        ), 
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='equirectangular'
        ),
        annotations = [dict(
                    x=0.50,
                    y=-0.1,
                    xref='paper',
                    yref='paper',
                    text='Source:<a href="https://www.numbeo.com/cost-of-living/rankings_by_country.jsp">\
                        Numbeo.com</a>',
                    showarrow = False
                )],)
    return figmap,year
@app.callback(
    Output("interval", "disabled"),
    Input("play", "n_clicks"),
    State("interval", "disabled"),
)
def toggle(n, playing):
    if n:
        return not playing
    return playing

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)