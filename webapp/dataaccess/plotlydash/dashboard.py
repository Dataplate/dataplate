"""Instantiate a Dash app."""
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash_extensions.enrich import Dash, ServersideOutput, Output, Input, Trigger, State
import dash_cytoscape as cyto
import numpy as np
import pandas as pd
from ..plotlydash import _protect_dashviews
from dash.exceptions import PreventUpdate

from .data import create_dataframe


def init_dashboard(server, login_reg=True):
    """Create a Plotly Dash dashboard."""

    # Meta tags for viewport responsiveness
    meta_viewport = {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}
    dash_app = dash.Dash(
        server=server,
        url_base_pathname='/admin/dashboard/',
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "/static/css/styles.css",
            "https://fonts.googleapis.com/css?family=Lato",
        ],
        meta_tags=[meta_viewport]
    )

    df = create_dataframe()

    elements = build_nodes_edges_for_cytoscape(df)

    # Create Layout
    dash_app.layout = html.Div(
        children=[
            dcc.Dropdown(id='dropdown', multi=True, placeholder="Select user(s)"),
            html.Div(id='dd-output-container'),
            dcc.Graph(
                id="histogram-graph",
                config = {'displayModeBar': False}
            ),
            dcc.Interval(
                id='interval-component',
                interval=60 * 1000,  # in milliseconds
                n_intervals=0
            ),
            cyto.Cytoscape(
                id='cytoscape-users-kinds',
                layout={
                    "title": "Actions Per User",
                    'name': 'cose'
                },
                style={'width': '100%', 'height': '400px'},
                elements=elements,
                stylesheet=[
                    # Group selectors
                    {
                        'selector': 'node',
                        'style': {
                            'content': 'data(label)'
                        }
                    },
                    # Class selectors
                    {
                        'selector': '.blue',
                        'style': {
                            'background-color': 'blue',
                            'line-color': 'blue'
                        }
                    },
                    {
                        'selector': '.green',
                        'style': {
                            'background-color': 'green',
                            'line-color': 'green'
                        }
                    }
                ]
            ),
            dash_table.DataTable(
                id="database-table",
                columns=[{"name": i, "id": i} for i in ['id','created_on','session_id','user','kind','text']
                         # omit the id column
                         if i != 'id'
                         ],
                style_table={'overflowX': 'auto'},
                style_cell_conditional=[
                    {'if': {'column_id': 'session_id'},
                     'width': '20px'},
                    {'if': {'column_id': 'kind'},
                     'width': '20px'},
                    {'if': {'column_id': 'user'},
                     'width': '40px'},
                ],
                style_cell={
                    'minWidth': '20px', 'width': '30px', 'maxWidth': '250px',
                    'whiteSpace': 'normal',
                },
                data=[],
                sort_action="native",
                sort_mode="multi",
                page_action="native",
                page_size=10,
                tooltip_data=[
                    {
                        column: {'value': str(value), 'type': 'markdown'}
                        for column, value in row.items()
                    } for row in (df.to_dict('records') if not df.empty else {})
                ],
                tooltip_duration=None,
                css=[{
                    'selector': '.dash-spreadsheet td div',
                    'rule': '''
                    line-height: 15px;
                    max-height: 30px; min-height: 30px; height: 30px;
                    display: block;
                    overflow-y: hidden;
                '''
                }],
            ),
        ],
        id="dash-container",
    )

    #, prevent_initial_call=True
    @dash_app.callback([Output('histogram-graph', 'figure'), Output('cytoscape-users-kinds', 'elements'), Output('database-table', 'data')], [Input('dropdown', 'value')], State('cytoscape-users-kinds', 'elements'))
    def update_output(value, elements):
        #figure=get_histogram_kind_figure(df),
        df1 = create_dataframe()
        if df1.empty:
            raise PreventUpdate
        if value:
            val_lst = []
            if isinstance(value, list):
                val_lst = value
            else:
                val_lst.append(value)
            df1 = df1[df1["user"].isin(val_lst)]
            elements = build_nodes_edges_for_cytoscape(df1)

        fig = get_histogram_kind_figure(df1)

        return [fig,elements,df1.to_dict("records")]

    @dash_app.callback(Output("dropdown", "options"), [Input("dropdown", "search_value")])
    def update_options(search_value):
        df = create_dataframe()
        if df.empty:
            raise PreventUpdate
            # return dash.no_update

        users_options = [{'label': i[0], 'value': i[0]} for i in df.groupby("user")['user']]
        search_value = [users_options[0]['value'] if users_options else '']

        return users_options

    # @dash_app.callback(Output('dropdown', 'value'),[Input('dropdown', 'options')])
    # def set_users_value(available_options):
    #     if not available_options:
    #         raise PreventUpdate
    #     return available_options[0]['value'] if available_options else ''

    # @dash_app.callback(Output('database-table', 'data'), Input('interval-component', 'n_intervals'))
    # def query_df(n):
    #     return create_dataframe().to_dict("records")


    if login_reg:
        _protect_dashviews(dash_app)

    return dash_app.server


def build_nodes_edges_for_cytoscape(df):
    if df.empty:
        return []

    s_users = df.groupby("user")['user']
    s_kinds = df.groupby("kind")['kind']

    nodes_users = [
        {
            'data': {'id': user, 'label': user},
            'classes': 'blue'  # Single class
        }
        for user in s_users.unique().index
    ]
    nodes_kinds = [
        {
            'data': {'id': kind, 'label': kind},
            'classes': 'green'  # Single class
        }
        for kind in s_kinds.unique().index
    ]
    df_filtered = df.copy()
    df_filtered.set_index(['user', 'kind'], inplace=True)
    edges = [
        {'data': {'source': user, 'target': kind}}
        for user, kind in df_filtered.index.to_list()
    ]

    elements = nodes_users + nodes_kinds + edges

    return elements

def get_histogram_kind_figure(df_for_fig):
    if df_for_fig.empty:
        raise PreventUpdate
    fig = dict({
            "data": [
                {
                    "x": df_for_fig["user"],
                    "text": df_for_fig["user"],
                    "customdata": df_for_fig["kind"],
                    "name": "Data access by users",
                    "type": "histogram",
                }
            ],
            "layout": {
                "title": "Data Access By Users",
                "height": 500,
                "padding": 150,
            },
        })

    return fig

def create_data_table(df):
    """Create Dash datatable from Pandas DataFrame."""
    if df.empty:
       raise PreventUpdate
    table = dash_table.DataTable(
        id="database-table",
        columns=[{"name": i, "id": i} for i in df.columns
                 # omit the id column
                 if i != 'id'
        ],
        style_table={'overflowX': 'auto'},
        style_cell_conditional=[
            {'if': {'column_id': 'session_id'},
             'width': '20px'},
            {'if': {'column_id': 'kind'},
             'width': '20px'},
            {'if': {'user': 'kind'},
             'width': '40px'},
        ],
        style_cell={
            'minWidth': '20px', 'width': '30px', 'maxWidth': '250px',
            'whiteSpace': 'normal',
        },
        data=df.to_dict("records"),
        sort_action="native",
        sort_mode="multi",
        page_action="native",
        page_size=10,
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in df.to_dict('records')
        ],
        tooltip_duration=None,
        css=[{
            'selector': '.dash-spreadsheet td div',
            'rule': '''
                line-height: 15px;
                max-height: 30px; min-height: 30px; height: 30px;
                display: block;
                overflow-y: hidden;
            '''
        }],
    )
    return table

#        filter_action="native",

 # dcc.Interval(
    #     id='interval-component',
    #     interval=5 * 1000,  # in milliseconds
    #     n_intervals=0
    # ),


    # @dash_app.callback(ServersideOutput("store", "data"), Trigger("onload", "children"))
    # def query_df():
    #     return create_dataframe()
