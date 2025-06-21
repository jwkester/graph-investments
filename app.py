import os
import sqlite3

import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from flask import Flask, render_template, request

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "investments.sqlite3")


def get_all_investment_names():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT DISTINCT Investment FROM investments", conn)
        return sorted(df['Investment'].dropna().unique())
    finally:
        conn.close()


def query_data(start_date=None, end_date=None, selected_names=None):
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM investments", conn)
    finally:
        conn.close()

    df.rename(columns={
        'Date': 'date',
        'Investment': 'investment_name',
        'Total': 'total'
    }, inplace=True)

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['total'] = pd.to_numeric(df['total'], errors='coerce')
    df = df.dropna(subset=['date', 'total'])
    df = df[df['date'].dt.year.isin([2024, 2025])]

    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]
    if selected_names:
        df = df[df['investment_name'].isin(selected_names)]

    return df


def generate_graphs(df):
    graphs_html = []
    for investment in df['investment_name'].unique():
        inv_df = df[df['investment_name'] == investment].copy()
        inv_df.sort_values('date', inplace=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=inv_df['date'].dt.strftime('%Y-%m-%d'),
            y=inv_df['total'],
            mode='lines+markers',
            name=investment
        ))
        fig.update_layout(
            title=f"Total Value Over Time: {investment}",
            xaxis_title="Date",
            yaxis_title="Total Value",
            xaxis=dict(tickformat="%m-%d-%y"),
            margin=dict(l=40, r=40, t=40, b=40),
            height=400
        )
        graphs_html.append(pio.to_html(fig, full_html=False))
    return graphs_html


@app.route("/", methods=["GET", "POST"])
def index():
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    selected_names = request.form.getlist("investment_name")
    all_names = get_all_investment_names()

    try:
        df = query_data(start_date, end_date, selected_names)
        graphs = generate_graphs(df)
    except Exception as e:
        graphs = [f"<p>Error: {str(e)}</p>"]

    return render_template("index.html", graphs=graphs, start_date=start_date,
                           end_date=end_date, all_names=all_names, selected_names=selected_names)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
