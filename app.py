import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import random

# Generate sample extended benchmark data for demonstration purposes
indicators = [
    "Energy Intensity", "GHG Emissions Reduction", "Waste Management", "Water Consumption",
    "Recycled Materials Usage", "Employee Health and Safety", "Supply Chain Emissions",
    "Biodiversity Impact", "Packaging Recyclability", "Community Engagement", "Product Carbon Footprint",
    "Renewable Energy Usage", "Material Efficiency", "Social Responsibility Initiatives", "Resource Conservation",
    "Air Quality Impact", "Water Quality Impact", "Recycling Efficiency", "Sustainable Sourcing", "Carbon Neutral Initiatives"
]
industries = ["food_packaging", "healthcare", "technology"]

# Generate random benchmark data for each industry
random.seed(42)
benchmark_data = {}
for industry in industries:
    benchmark_data[industry] = {
        "Indicator": indicators,
        "Average Benchmark": [random.uniform(10, 100) for _ in indicators]
    }

# Convert to DataFrame
benchmark_dfs = {industry: pd.DataFrame(data) for industry, data in benchmark_data.items()}

# Instantiate the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

# Layout for the dashboard
app.layout = dbc.Container([
    html.H1("Generative AI-Based ESG Analysis System"),

    # Industry selection dropdown
    html.Label("Select Industry:"),
    dcc.Dropdown(
        id='industry-dropdown',
        options=[
            {'label': 'Food Packaging', 'value': 'food_packaging'},
            {'label': 'Healthcare', 'value': 'healthcare'},
            {'label': 'Technology', 'value': 'technology'}
        ],
        value='food_packaging',
        style={'width': '50%'}
    ),

    html.Br(),
    html.H4("Industry Benchmarks"),

    # Sample line charts for first 4 indicators
    html.Div([
        dcc.Graph(id='line-chart-1'),
        dcc.Graph(id='line-chart-2'),
        dcc.Graph(id='line-chart-3'),
        dcc.Graph(id='line-chart-4'),
    ], style={'display': 'flex', 'flex-wrap': 'wrap'}),

    # Industry Benchmarks Table
    html.Div(id='industry-benchmark-table', children=[]),

    html.Br(),
    html.Label("Upload ESG Report for Analysis:"),

    # File upload button
    dcc.Upload(
        id='upload-esg-report',
        children=html.Button('Upload ESG Report'),
        multiple=False
    ),

    html.Br(),
    html.Label("Select ESG Indicators of Interest:"),

    # ESG Indicator multi-selection
    dcc.Checklist(
        id='esg-indicator-checklist',
        options=[{'label': indicator, 'value': indicator} for indicator in indicators],
        value=indicators,
        inline=True
    ),

    html.Br(),
    html.H4("Comparison Results"),

    # Comparison Results Table
    html.Div(id='comparison-results-table', children=[]),
], fluid=True)

# Callback for updating industry benchmark table and line charts
@app.callback(
    [
        Output('industry-benchmark-table', 'children'),
        Output('line-chart-1', 'figure'),
        Output('line-chart-2', 'figure'),
        Output('line-chart-3', 'figure'),
        Output('line-chart-4', 'figure')
    ],
    [Input('industry-dropdown', 'value')]
)
def update_industry_benchmark_table(selected_industry):
    benchmark_df = benchmark_dfs[selected_industry]

    # Create the benchmark table
    table_fig = dcc.Graph(figure=go.Figure(data=[go.Table(
        header=dict(values=list(benchmark_df.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[benchmark_df.Indicator, benchmark_df['Average Benchmark']],
                   fill_color='lavender',
                   align='left')
    )]))

    # Create sample line charts for the first 4 indicators
    years = [2018, 2019, 2020, 2021, 2022, 2023]
    line_figs = []
    for i in range(4):
        values = [random.uniform(10, 100) for _ in years]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=years, y=values, mode='lines+markers', name=benchmark_df['Indicator'][i]))
        fig.update_layout(title=f"{benchmark_df['Indicator'][i]} Benchmark Over Time",
                          xaxis_title='Year',
                          yaxis_title='Benchmark Value')
        line_figs.append(fig)

    return table_fig, line_figs[0], line_figs[1], line_figs[2], line_figs[3]

# Callback for handling ESG report upload and indicator selection
@app.callback(
    Output('comparison-results-table', 'children'),
    [Input('upload-esg-report', 'contents'), Input('esg-indicator-checklist', 'value')]
)
def update_comparison_results(uploaded_file, selected_indicators):
    if uploaded_file is None:
        return html.Div("Please upload an ESG report for analysis.")

    # Dummy implementation for uploaded ESG report parsing
    # In real-world use, we would parse the uploaded PDF or CSV file here
    parsed_data = {
        "Indicator": selected_indicators,
        "Company Value": [random.uniform(10, 100) for _ in selected_indicators]  # Placeholder values
    }
    parsed_df = pd.DataFrame(parsed_data)

    benchmark_df = benchmark_dfs['food_packaging']  # Defaulting to food packaging for simplicity
    comparison_df = benchmark_df[benchmark_df['Indicator'].isin(selected_indicators)].copy()
    comparison_df['Company Value'] = parsed_df['Company Value']
    comparison_df['Performance'] = comparison_df.apply(
        lambda row: 'Above Average' if row['Company Value'] <= row['Average Benchmark'] else 'Needs Improvement',
        axis=1
    )

    comparison_table = dcc.Graph(figure=go.Figure(data=[go.Table(
        header=dict(values=list(comparison_df.columns),
                    fill_color='paleturquoise',
                    align='left'),
        cells=dict(values=[comparison_df.Indicator, comparison_df['Average Benchmark'], comparison_df['Company Value'], comparison_df['Performance']],
                   fill_color='lavender',
                   align='left')
    )]))
    return comparison_table

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
