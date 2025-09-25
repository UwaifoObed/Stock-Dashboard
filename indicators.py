# RSI Calculation
def calculation_rsi(data, window=14):
    delta = data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain/loss
    rsi = 100 - (100 / (1 + rs))
    data["RSI"] = rsi
    return data

# Bollinger Bands
def calculate_bollinger(data, window=20):
    rolling_mean = data["Close"].rolling(window).mean()
    rolling_std = data["Close"].rolling(window).std()

    data["BB_Middle"] = rolling_mean
    data["BB_Upper"] = rolling_mean + (2 * rolling_std)
    data["BB_Lower"] = rolling_mean - (2 * rolling_std)
    return data

# MACD
def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    short_ema = data["Close"].ewm(span=short_window, adjust=False).mean()
    long_ema = data["Close"].ewm(span=long_window, adjust=False).mean()

    data["MACD"] = short_ema - long_ema
    data["Signal_Line"] = data["MACD"].ewm(span=signal_window, adjust=False).mean()
    data["MACD_Hist"] = data["MACD"] - data["Signal_Line"]
    return data


# buttons = []

# if rsi_indices:
#     buttons.append(dict(
#         label="Toggle RSI", 
#         method="update",
#         args=[{"visible": [
#             (i == rsi_indices) ^ trace.visible
#             if i in rsi_indices else trace.visible
#             for i, trace in enumerate(fig.data)
#         ]}]
#     ))

# if macd_indices:
#     buttons.append(dict(
#         label="Toggle MACD", 
#         method="update",
#         args=[{"visible": [
#             (i == macd_indices) ^ trace.visible
#             if i in macd_indices else trace.visible
#             for i, trace in enumerate(fig.data)
#         ]}]
#     ))

# # Layout
# fig.update_layout(
#     updatemenus=[
#         dict(
#             type="buttons",
#             direction="down",
#             x=1.1,y=1,
#             showactive=True,
#             buttons=buttons
#         )
#     ]
# )