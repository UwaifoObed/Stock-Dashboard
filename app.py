import streamlit as st
from datetime import datetime
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import io
from indicators import calculate_bollinger, calculate_macd, calculation_rsi
from plotly.subplots import make_subplots


st.title("📊 Stock Market Dashboard")
st.subheader("Powered by Streamlit & Yahoo Finance")

# -----------------------------------
# Sidebar
# -----------------------------------
st.sidebar.title("Dashboard Settings")

# Stock Ticker Input
user_input = st.sidebar.text_input("Enter Stock", "AAPL")

# Date Presets
preset_options = ["None", "1-Month", "6-Months", "1-Year", "5-Years", "Max"]
date_presets = st.sidebar.selectbox("Date Presets", preset_options)

today = datetime.now()

if date_presets == "None":
    # Manual Date Input
    specific_date = datetime(2015, 1, 1)
    start_date_input = st.sidebar.date_input("Start Date", specific_date)
    end_date_input = st.sidebar.date_input("End Date", today)

    start_date_input = datetime.combine(start_date_input, datetime.min.time())
    end_date_input = datetime.combine(end_date_input, datetime.min.time())
else:
    if date_presets == "1-Month":
        start_date_input = today - pd.DateOffset(months=1)
    elif date_presets == "6-Months":
        start_date_input = today - pd.DateOffset(months=6)
    elif date_presets == "1-Year":
        start_date_input = today - pd.DateOffset(years=1)
    elif date_presets == "5-Years":
        start_date_input = today - pd.DateOffset(years=5)
    elif date_presets == "Max":
        start_date_input = datetime(1980, 1, 1)

    end_date_input = today

# -----------------------------------
# Indicators
# -----------------------------------
seven_day = st.sidebar.checkbox("7-day Moving Average")
thirty_day = st.sidebar.checkbox("30-day Moving Average")
ema_check = st.sidebar.checkbox("EMA (20)")
rsi_check = st.sidebar.checkbox("RSI (14)")
bollinger_check = st.sidebar.checkbox("Bollinger Bands (20)")
macd_check = st.sidebar.checkbox("MACD (12,26,9)")

# Comparison Mode
options = ["AAPL", "MSFT", "TSLA", "IBM"]
stock_mode = st.sidebar.multiselect("Select stocks", options)
stock_mode = [ticker for ticker in stock_mode if ticker != user_input]

# Chart type
chart_type = st.sidebar.radio(
    "Chart Type",
    ("Candlestick","Line Chart")
)

# -----------------------------------
# Download stock data
# -----------------------------------
raw = yf.download(user_input, start=start_date_input, end=end_date_input, auto_adjust=False)

# Flatten MultiIndex columns if needed
if isinstance(raw.columns, pd.MultiIndex):
    raw.columns = [col[0] for col in raw.columns]

if raw.empty:
    st.warning("No data returned. Check ticker or date range.")
else:
    st.write("Preview of download data:")
    st.dataframe(raw.tail(10))

# Reset index and prep
raw = raw.reset_index()
raw["Date"] = pd.to_datetime(raw["Date"])
for c in ["Open", "High", "Low", "Close"]:
    raw[c] = pd.to_numeric(raw[c], errors="coerce")

simplify = st.sidebar.checkbox("Simplify Chart (Weekly Data)")
if simplify:
    raw = raw.resample("W", on="Date").agg({"Open":"first", "High":"max", "Low":"min", "Close":"last", "Volume":"sum"}).reset_index()

# Moving averages
raw["7MA"] = raw["Close"].rolling(7, min_periods=1).mean()
raw["30MA"] = raw["Close"].rolling(30, min_periods=1).mean()
raw["EMA20"] = raw["Close"].ewm(span=20, adjust=False).mean()

# Base chart
price_height = 0.6
remaining = 1.0 - price_height
if rsi_check and macd_check:
    rsi_height = macd_height = remaining / 2
elif rsi_check:
    rsi_height, macd_height = remaining, 0
elif macd_check:
    macd_height, rsi_height = remaining, 0
else:
    rsi_height = macd_height = 0

# -----------------------------------
# Subplot rows setup
# -----------------------------------
row_heights = [0.6, 0.2] # Price + Volume always
if rsi_check and macd_check:
    row_heights.extend([0.1, 0.1])
elif rsi_check:
    row_heights.append(0.2)
elif macd_check:
    row_heights.append(0.2)

n_rows = len(row_heights)

specs = [[{"type": "xy"}] for _ in range(n_rows)]

# -----------------------------------
# Create subplots layout
# -----------------------------------
fig = make_subplots(
    rows=n_rows, 
    cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.05, 
    row_heights=row_heights
)

price_row = 1
volume_row = 2
rsi_row = 3 if rsi_check else None
macd_row = 4 if (macd_check and rsi_check) else (3 if macd_check else None)

# Prevent candlestick when comparing
if stock_mode and chart_type == "Candlestick":
    st.warning("Candlestick charts are only available for a single stock. Switching to Line Chart.")
    chart_type = "Line Chart"

if chart_type == "Candlestick":
    fig.add_trace(go.Candlestick(
        x=raw["Date"],
        open=raw["Open"],
        high=raw["High"],
        low=raw["Low"],
        close=raw["Close"],
        name=f"{user_input} Candles",
        increasing=dict(line=dict(color="green", width=1), fillcolor="green"),
        decreasing=dict(line=dict(color="red", width=1), fillcolor="red"),
        showlegend=False
    ),
    row=price_row, col=1
    )

elif chart_type == "Line Chart":
    fig.add_trace(go.Scatter(
        x=raw["Date"],
        y=raw["Close"],
        mode="lines",
        name=f"{user_input} Close"
    ),
    row=price_row, col=1
    )

# Moving averages
if chart_type == "Line Chart":
    if seven_day:
        fig.add_trace(go.Scatter(
            x=raw["Date"],
            y=raw["7MA"],
            mode="lines",
            name="7-day MA",
            line=dict(width=1.5)
        ),
        row=price_row, col=1
        )

    if thirty_day:
        fig.add_trace(go.Scatter(
            x=raw["Date"],
            y=raw["30MA"],
            mode="lines",
            name="30-day MA",
            line=dict(width=1.5)
        ),
        row=price_row, col=1
        )

    if ema_check:
        fig.add_trace(go.Scatter(
            x=raw["Date"],
            y=raw["EMA20"],
            mode="lines",
            name="EMA (20)",
            line=dict(width=1.5, dash="dot", color="orange")
        ), row=price_row, col=1)

# Group indicators under one legend group
fig.update_traces(legendgroup="Indicators", selector=dict(name="7-day MA"))
fig.update_traces(legendgroup="Indicators", selector=dict(name="30-day MA"))
fig.update_traces(legendgroup="Indicators", selector=dict(name="EMA (20)"))
fig.update_traces(legendgroup="Indicators", selector=dict(name="BB Upper"))
fig.update_traces(legendgroup="Indicators", selector=dict(name="BB Middle"))
fig.update_traces(legendgroup="Indicators", selector=dict(name="BB Lower"))

# -----------------------------------
# Bollinger Bands Subplot
# -----------------------------------
if bollinger_check:
    raw = calculate_bollinger(raw)

    fig.add_trace(
        go.Scatter(
            x=raw["Date"],
            y=raw["BB_Upper"],
            line=dict(width=0.5),
            name="BB Upper",
            showlegend=True
        ),
        row=price_row, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=raw["Date"],
            y=raw["BB_Lower"],
            line=dict(width=0.5),
            name="BB Lower",
            fill="tonexty",
            fillcolor="rgba(150,150,150,0.2)",
            showlegend=True
        ),
        row=price_row, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=raw["Date"],
            y=raw["BB_Middle"],
            line=dict(width=0.5, dash="dash"),
            name="BB Middle"
        ),
        row=price_row, col=1
    )

# Comparison stocks
if stock_mode:
    comp_data = yf.download(stock_mode, start=start_date_input, end=end_date_input, auto_adjust=True)
    if isinstance(comp_data.columns, pd.MultiIndex):
        comp_data.columns = [c[0] for c in comp_data.columns]
    comp_data = comp_data.reset_index()
    comp_data["Date"] = pd.to_datetime(comp_data["Date"])

    normalize = st.sidebar.checkbox("Show Normalized Prices (100=Start)", value=(len(stock_mode) > 1))

    if isinstance(comp_data["Close"], pd.Series):  # single ticker
        if normalize:
            y_data = comp_data["Close"] / comp_data["Close"].iloc[0] * 100
            y_label = "Normalized (100=Start)"
        else:
            y_data = comp_data["Close"]
            y_label = "Actual Close"

        fig.add_trace(go.Scatter(
            x=comp_data["Date"],
            y=y_data,
            mode="lines",
            name=f"{stock_mode[0]} {y_label}"
        ))
    else:  # multiple tickers
        for ticker in stock_mode:
            if not comp_data.empty:
                if normalize:
                    y_data = comp_data["Close"][ticker] / comp_data["Close"][ticker].iloc[0] * 100
                    y_label = "Normalized (100=Start)"
                else:
                    y_data = comp_data["Close"][ticker]
                    y_label = "Actual Close"

                fig.add_trace(go.Scatter(
                    x=comp_data["Date"],
                    y=y_data,
                    mode="lines",
                    name=f"{ticker} {y_label}"
                ))

# -----------------------------------
# RSI Subplot
# -----------------------------------
if rsi_check:
    raw = calculation_rsi(raw)
    trace = go.Scatter(
            x=raw["Date"],
            y=raw["RSI"],
            mode="lines",
            name="RSI"
        )
    fig.add_trace(trace, row=rsi_row, col=1)
    fig.add_hline(y=70, line=dict(color="red", dash="dash"), row=rsi_row, col=1)
    fig.add_hline(y=30, line=dict(color="green", dash="dash"), row=rsi_row, col=1)
    fig.update_yaxes(range=[0, 100], row=rsi_row, col=1)

# -----------------------------------
# MACD Subplot
# -----------------------------------
if macd_check:
    raw = calculate_macd(raw)
    hist_colors = ["green" if v >= 0 else "red" for v in raw["MACD_Hist"].fillna(0)]

    fig.add_trace(
        go.Bar(
            x=raw["Date"],
            y=raw["MACD_Hist"],
            name="MACD_Hist",
            marker_color=hist_colors
        ),
        row=macd_row, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=raw["Date"],
            y=raw["MACD"],
            mode="lines",
            name="MACD"
        ),
        row=macd_row, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=raw["Date"],
            y=raw["Signal_Line"],
            mode="lines",
            name="Signal"
        ),
        row=macd_row, col=1
    )

# Volume Bars
colors = ["green" if c > o else "red" for c, o in zip(raw["Close"], raw["Open"])]

fig.add_trace(
    go.Bar(
        x=raw["Date"],
        y=raw["Volume"],
        name="Volume",
        marker=dict(color=colors, line=dict(width=0)),
        opacity=1
    ),
    row=volume_row, col=1
)

# Title
if stock_mode:
    chart_title = f"{user_input} vs {', '.join(stock_mode)} Closing Prices"
else:
    chart_title = f"{user_input} Closing Price"

# -----------------------------------
# Log scale option
# -----------------------------------
log_scale = st.sidebar.checkbox("Logarithmic Scale (Y-axis)")
if log_scale:
    fig.update_yaxes(type="log")

st.sidebar.subheader("Download Data")

# -----------------------------------
# To download CSV file
# -----------------------------------
csv_data = raw.to_csv(index=False).encode("utf-8")

# -----------------------------------
# CSV Download Button
# -----------------------------------
st.sidebar.download_button(
    label="⬇️ Download CSV",
    data=csv_data,
    file_name="data.csv",
    mime="text/csv"
)

# -----------------------------------
# To download excel file
# -----------------------------------
excel_buffer = io.BytesIO()

# Try using xlsxwriter, else fall back to openpyxl
try:
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        raw.to_excel(writer, index=False, sheet_name="StockData")
    
except ModuleNotFoundError:
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        raw.to_excel(writer, index=False, sheet_name="StockData")

excel_data = excel_buffer.getvalue()

# -----------------------------------
# Excel Download button
# -----------------------------------
st.sidebar.download_button(
    label="⬇️ Download Excel",
    data=excel_data,
    file_name=f"{user_input}_stock_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

fig.update_layout(
    plot_bgcolor="black",
    paper_bgcolor="black",
    font=dict(color="#e0e0e0"),
    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)"),
    title=dict(text=chart_title, x=0.5),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
)

# make rangeslider visible on price subplot only
fig.update_xaxes(rangeslider_visible=True, row=price_row, col=1)

# Axis labels
fig.update_yaxes(title_text="Price", row=price_row, col=1, side="left")
fig.update_yaxes(title_text="Volume", row=volume_row, col=1, side="right", showgrid=False, rangemode="tozero")

# Show chart
st.plotly_chart(fig, use_container_width=True)