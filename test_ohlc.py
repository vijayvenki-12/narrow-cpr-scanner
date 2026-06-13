from SmartApi import SmartConnect
import os
import urllib
import json
import pandas as pd
import datetime as dt
from pyotp import TOTP
import time
from pathlib import Path


key_path = r"C:\Users\Lenovo\PycharmProjects\Angelone_api\Narrow_cpr_scanner"
os.chdir(key_path)

key_secret = open("key.txt", "r").read().split()

obj = SmartConnect(api_key=key_secret[0])
data = obj.generateSession(key_secret[2], key_secret[3], TOTP(key_secret[4]).now())

with open(
    r"C:\Users\Lenovo\PycharmProjects\Angelone_api\Narrow_cpr_scanner\data\instruments.json",
    "r"
) as f:
    instrument_list = json.load(f)

print(f"Loaded {len(instrument_list)} instruments")

def token_lookup(ticker, instrument_list, exchange="NSE"):
    for instrument in instrument_list:
        if instrument["name"] == ticker and instrument["exch_seg"] == exchange and instrument["symbol"].split('-')[
            -1] == "EQ":
            return instrument["token"]


def symbol_lookup(token, instrument_list, exchange="NSE"):
    for instrument in instrument_list:
        if instrument["token"] == token and instrument["exch_seg"] == exchange and instrument["symbol"].split('-')[
            -1] == "EQ":
            return instrument["name"]


def hist_data(tickers, duration, interval, instrument_list, exchange="NSE"):
    hist_data_tickers = {}

    for ticker in tickers:

        token = token_lookup(ticker, instrument_list)
        if token is None:
            print(f"Token not found for {ticker}")
            continue
        params = {
            "exchange": exchange,
            "symboltoken": token,
            "interval": interval,
            "fromdate": (dt.datetime.now() - dt.timedelta(days=duration)).strftime("%Y-%m-%d 09:15"),
            "todate": dt.datetime.now().strftime("%Y-%m-%d 15:30")
        }

        print(f"\nFetching {ticker}")

        response = None

        for attempt in range(3):

            try:
                time.sleep(3)

                response = obj.getCandleData(params)

                if response and response.get("status"):
                    print(f"Success: {ticker}")
                    break

            except Exception as e:
                print(f"{ticker} attempt {attempt + 1}: {e}")
                time.sleep(3)

        if not response or not response.get("status"):
            print(f"Skipping {ticker}")
            continue

        df_data = pd.DataFrame(
            response["data"],
            columns=["date", "open", "high", "low", "close", "volume"]
        )

        df_data.set_index("date", inplace=True)

        hist_data_tickers[ticker] = df_data

    return hist_data_tickers


candle_data = hist_data(["ADANIGREEN",  "ABCAPITAL", "ABFRL", "ALKEM", "AMBUJACEM", "ANGELONE", "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY",
    "ASIANPAINT", "ASTRAL", "ATUL", "AUBANK", "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE",
    "BAJAJFINSV", "BALKRISIND", "BALRAMCHIN", "BANDHANBNK", "BANKBARODA", "BANKINDIA", "BATAINDIA",
    "BEL", "BERGEPAINT", "BHARATFORG", "BHEL", "BPCL", "BHARTIARTL", "BIOCON", "BOSCHLTD", "BRITANNIA",
    "BSE", "BSOFT", "CANBK", "CANFINHOME", "CDSL", "CHAMBLFERT", "CHOLAFIN", "CIPLA", "COALINDIA",
    "COFORGE", "COLPAL", "CONCOR", "COROMANDEL", "CROMPTON", "CUB", "CUMMINSIND", "CYIENT", "DABUR",
    "DALBHARAT", "DEEPAKNTR", "DELHIVERY", "DIVISLAB", "DIXON", "DLF", "DMART", "DRREDDY", "EICHERMOT",
    "ESCORTS", "FEDERALBNK", "GAIL", "GLENMARK", "GMRINFRA", "GNFC", "GODREJCP", "GRASIM", "GUJGASLTD",
    "HAVELLS", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK"], 3, "ONE_DAY", instrument_list)



def calculate_cpr(df):

    last_day = df.iloc[-2]

    high = last_day["high"]
    low = last_day["low"]
    close = last_day["close"]

    pivot = (high + low + close) / 3

    raw_bc = (high + low) / 2
    raw_tc = (2 * pivot) - raw_bc

    bc = min(raw_bc, raw_tc)
    tc = max(raw_bc, raw_tc)

    width = tc - bc

    cpr_percent = (width / pivot) * 100

    return {
        "pivot": round(float(pivot), 2),
        "bc": round(float(bc), 2),
        "tc": round(float(tc), 2),
        "width": round(float(width), 2),
        "cpr_percent": round(float(cpr_percent), 4)
    }

for symbol in candle_data:

    cpr = calculate_cpr(candle_data[symbol])

    print(symbol, cpr["cpr_percent"])

narrow_cpr = []

for symbol in candle_data:

    cpr = calculate_cpr(candle_data[symbol])

    if cpr["cpr_percent"] < 0.1:
        narrow_cpr.append(symbol)

print("\nNarrow CPR Stocks")
print(narrow_cpr)


def get_ltp(symbol, instrument_list):

    token = token_lookup(symbol, instrument_list)

    response = obj.ltpData(
        "NSE",
        symbol,
        token
    )

    return response["data"]["ltp"]

def get_cpr_status(ltp, bc, tc):

    if ltp > tc:
        return "ABOVE_CPR"

    elif ltp < bc:
        return "BELOW_CPR"

    else:
        return "INSIDE_CPR"


def get_market_depth(symbol, instrument_list):

    token = token_lookup(symbol, instrument_list)

    exchangeTokens = {
        "NSE": [token]
    }

    response = obj.getMarketData(
        "FULL",
        exchangeTokens
    )

    data = response["data"]["fetched"][0]

    buy_qty = data["totBuyQuan"]
    sell_qty = data["totSellQuan"]

    return buy_qty, sell_qty

results = []

for symbol in candle_data:

    cpr = calculate_cpr(candle_data[symbol])

    ltp = get_ltp(symbol, instrument_list)

    buy_qty, sell_qty = get_market_depth(
        symbol,
        instrument_list
    )

    cpr_status = get_cpr_status(
        ltp,
        cpr["bc"],
        cpr["tc"]
    )

    results.append({
        "symbol": symbol,
        "pivot": cpr["pivot"],
        "bc": cpr["bc"],
        "tc": cpr["tc"],
        "width": cpr["width"],
        "cpr_percent": cpr["cpr_percent"],
        "ltp": ltp,
        "buy_qty": buy_qty,
        "sell_qty": sell_qty,
        "cpr_status": cpr_status
    })

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="cpr_percent",
    ascending=True
)

results_df.reset_index(drop=True, inplace=True)

results_df["narrow_cpr"] = (
    results_df["cpr_percent"] < 0.1
)

print(results_df)




