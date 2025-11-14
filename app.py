import os
import sqlite3
import numpy as np

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
    # df = df[df['date'].dt.year.isin([2024, 2025])]

    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]
    if selected_names:
        df = df[df['investment_name'].isin(selected_names)]

    return df


def generate_graphs(filtered_df, full_df, show_total_portfolio=False, show_total_non_cash=False):
    graphs_html = []
    for investment in filtered_df['investment_name'].unique():
        inv_df = filtered_df[filtered_df['investment_name'] == investment].copy()
        inv_df.sort_values('date', inplace=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=inv_df['date'].dt.strftime('%Y-%m-%d'),
            y=inv_df['total'],
            mode='lines+markers',
            name=investment
        ))
        # Add linear trendline for this investment
        if len(inv_df) >= 2:
            x_num = inv_df['date'].map(pd.Timestamp.toordinal).to_numpy()
            y = inv_df['total'].to_numpy()
            m, b = np.polyfit(x_num, y, 1)
            y_trend = m * x_num + b

            fig.add_trace(go.Scatter(
                x=inv_df['date'].dt.strftime('%Y-%m-%d'),
                y=y_trend,
                mode='lines',
                name=f"{investment} trend",
                line=dict(dash='dash')
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

    if show_total_portfolio:
        total_df = full_df.groupby('date')['total'].sum().reset_index()
        total_df.sort_values('date', inplace=True)
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(
            x=total_df['date'],
            y=total_df['total'],
            mode='lines+markers',
            name='Total Portfolio'
        ))
        # Add linear trendline for total portfolio
        if len(total_df) >= 2:
            x_num = total_df['date'].map(pd.Timestamp.toordinal).to_numpy()
            y = total_df['total'].to_numpy()
            m, b = np.polyfit(x_num, y, 1)
            y_trend = m * x_num + b

            fig_total.add_trace(go.Scatter(
                x=total_df['date'],
                y=y_trend,
                mode='lines',
                name='Total Portfolio trend',
                line=dict(dash='dash')
            ))
        fig_total.update_layout(
            title="Total Portfolio Over Time",
            xaxis_title="Date",
            yaxis_title="Total Value",
            xaxis=dict(tickformat="%m-%d-%y"),
            margin=dict(l=40, r=40, t=40, b=40),
            height=400
        )
        graphs_html.append(pio.to_html(fig_total, full_html=False))

    if show_total_non_cash:
        non_cash_df = full_df[full_df['investment_name'] != 'VMFXX']
        non_cash_sum = non_cash_df.groupby('date')['total'].sum().reset_index()
        non_cash_sum.sort_values('date', inplace=True)
        fig_non_cash = go.Figure()
        fig_non_cash.add_trace(go.Scatter(
            x=non_cash_sum['date'],
            y=non_cash_sum['total'],
            mode='lines+markers',
            name='Total Non-Cash'
        ))
        # Add linear trendline for total non-cash
        if len(non_cash_sum) >= 2:
            x_num = non_cash_sum['date'].map(pd.Timestamp.toordinal).to_numpy()
            y = non_cash_sum['total'].to_numpy()
            m, b = np.polyfit(x_num, y, 1)
            y_trend = m * x_num + b

            fig_non_cash.add_trace(go.Scatter(
                x=non_cash_sum['date'],
                y=y_trend,
                mode='lines',
                name='Total Non-Cash trend',
                line=dict(dash='dash')
            ))
        fig_non_cash.update_layout(
            title="Total Non-Cash Investments Over Time",
            xaxis_title="Date",
            yaxis_title="Total Value",
            xaxis=dict(tickformat="%m-%d-%y"),
            margin=dict(l=40, r=40, t=40, b=40),
            height=400
        )
        graphs_html.append(pio.to_html(fig_non_cash, full_html=False))

    return graphs_html


@app.route("/", methods=["GET", "POST"])
def index():
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    selected_names = request.form.getlist("investment_name")
    show_total_portfolio = 'show_total_portfolio' in request.form
    show_total_non_cash = 'show_total_non_cash' in request.form
    all_names = get_all_investment_names()
    try:
        full_df = query_data(start_date=start_date, end_date=end_date)  # filter by date only
        df = query_data(start_date, end_date, selected_names)  # filter by date and investment
        graphs = generate_graphs(df, full_df, show_total_portfolio, show_total_non_cash)
    except Exception as e:
        graphs = [f"<p>Error: {str(e)}</p>"]

    return render_template("index.html", graphs=graphs, start_date=start_date,
                           end_date=end_date, all_names=all_names, selected_names=selected_names,
                           show_total_portfolio=show_total_portfolio, show_total_non_cash=show_total_non_cash)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
