# -*- coding: utf-8 -*-
"""
Created on Fri Dec 18 14:02:39 2020

@author: Andre
need to upload t-SNE csv and FEMA mitigations csv to a github for this
"""
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.offline import plot

df = pd.read_csv('https://raw.githubusercontent.com/andrewhong5297/flood_dash_app/main/HazardMitigationAssistanceProjects.csv')
df["projectAmountMillions"]=df["projectAmount"].div(1000000)

regions = pd.read_csv('https://raw.githubusercontent.com/andrewhong5297/flood_dash_app/main/States_Abrev_Regions.csv')
state_region_dict = dict(zip(regions["State"],regions["Region"]))
def state_to_region(x):
    try:
        region_result = state_region_dict[x]
        return region_result
    except:
        print("result not found for {}, skipping".format(x))
    return "skip"

###State pivot
pivot_state = df.pivot_table(index="state",values=["projectAmountMillions", "numberOfProperties"],
                       aggfunc="sum")
pivot_state.reset_index(inplace=True)
pivot_state["region"]=pivot_state["state"].apply(lambda x: state_to_region(x))
pivot_state = pivot_state[pivot_state["region"]!="skip"] #removing regions not included in 50 states

'''plotly and dash app requires all the setup above'''
###plotly express scatter, for dash app later
import plotly.express as px
from plotly.offline import plot
available_states = pivot_state['state'].unique()
fig_px_fema = px.scatter(pivot_state, x="numberOfProperties", y="projectAmountMillions", hover_data=['state','region'],color="region")

PCA_components = pd.read_csv('https://raw.githubusercontent.com/andrewhong5297/flood_dash_app/main/cosine_tsne.csv')
PCA_components.dropna(inplace=True)
fig_px = px.scatter(PCA_components, x="tsne-2d-one", y="tsne-2d-two", hover_data=['Legislature','Regions','Agg_Name','Bill_Status'],color="State",opacity=0.7) #make color all blue though

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

FEMA_tab = dbc.Card(
                dbc.CardBody([
                        html.H5("Choose a State to see count of top 15 FEMA Mitigation Projects by Type"),
                        dbc.Row([
                            dbc.Col(
                            html.Div(
                            dcc.Dropdown(
                                    id='State_Search',
                                    options=[{'label': i, 'value': i} for i in available_states]
                                    , value="New York",
                                    multi=False
                                    ),
                                ),
                                width=6),
                            ]),
                    
                        dbc.Row([                        
                              dbc.Col(
                              dcc.Graph(id = "bar_plot", style={'height': '500px'})
                              ,width=10),
                        
                            html.H5("Total Project Amount and Number of Properties Covered In FEMA Projects by US State"),
                            dcc.Graph(figure = fig_px_fema, style={'height': '500px'}),
                            
                            ]),
                        ]),
                    className="mt-3",
                    ) #card end

@app.callback(
    Output('bar_plot', 'figure'),
    [Input('State_Search', 'value')])
def set_state_options(selection):
    temp_df = df[df["state"]==selection]
    projectTypeBar = temp_df["projectType"].value_counts()[:15]
    return px.bar(temp_df, x=projectTypeBar,y=projectTypeBar.index)

bills_tab = dbc.Card(
                dbc.CardBody([
                        # '''bill_flood stuff,should go in it's own tab later'''
                        dbc.Row([
                            html.H5("Hover over a bill (dot) to see the summary"),
                            ]),
                        dbc.Row([
                            html.Div("You can double click on a state in the legend to see bills from only that state"),
                            ]),
                
                        dbc.Row([                        
                              dbc.Col(
                              dcc.Graph(id = "plot", figure=fig_px, style={'height': '500px'})
                              ,width=10),
                        ]),
                          dbc.Row([
                            html.Div(id = "bill_summary"),
                            ]),
                            ]),
                    className="mt-3",
                    ) #card end

@app.callback(
    Output('bill_summary', 'children'),
    [Input('plot', 'hoverData')])
def show_bill_summary(data):
    bill_summary = PCA_components[PCA_components["Agg_Name"]==data["points"][0]["customdata"][2]]
    bill_summary = bill_summary["Summary"][bill_summary["Summary"].index[0]] #indexing
    return "Summary: {}".format(bill_summary)

author_tab = dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row([
                            html.H2('Created by Andrew Hong'),
                        ]),
                        
                        dbc.Row([
                            html.Label('This dashboard was created to help track unemployment through the Covid19 crisis, and see where disparities pop up during recovery. Please check the Medium blog post for data sourcing and methodology.'),
                        ]),
                        
                        dbc.Row([
                            dcc.Link('Medium Page', href="https://medium.com/@andrew.hong"),
                        ]),
                        
                        dbc.Row([
                            dcc.Link('LinkedIn', href = "https://www.linkedin.com/in/andrew-hong-nyu/"),
                        ]),
                    ]
                ),
            className="mt-3",
            )

app.layout = html.Div([

    dbc.Tabs([
        dbc.Tab(FEMA_tab, label="FEMA Projects"),
        dbc.Tab(bills_tab, label="Environmental State Bills"),
        dbc.Tab(author_tab, label="About Me", tab_style={"margin-left": "auto"}, label_style={"color": "#00AEF9"}),
        ])
    ])

if __name__ == '__main__':
    app.run_server(debug=False)