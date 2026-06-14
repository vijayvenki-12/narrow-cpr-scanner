from SmartApi import SmartConnect
import os
import json
import pandas as pd
import datetime as dt
from pyotp import TOTP
import time
from pathlib import Path

# ─── Resolve base directory dynamically (works on any OS / Render / Replit) ──
BASE_DIR = Path(__file__).resolve().parent

# ─── Load credentials from environment variables (never from key.txt) ────────
API_KEY     = os.environ.get("ANGEL_API_KEY")
CLIENT_ID   = os.environ.get("ANGEL_CLIENT_ID")
PIN         = os.environ.get("ANGEL_PIN")
TOTP_SECRET = os.environ.get("ANGEL_TOTP_SECRET")

if not all([API_KEY, CLIENT_ID, PIN, TOTP_SECRET]):
    raise EnvironmentError(
        "Missing one or more required environment variables: "
        "ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PIN, ANGEL_TOTP_SECRET"
    )

# ─── Login to Angel One ───────────────────────────────────────────────────────
obj  = SmartConnect(api_key=API_KEY)
data = obj.generateSession(CLIENT_ID, PIN, TOTP(TOTP_SECRET).now())

# ─── Load instruments from relative path ─────────────────────────────────────
instruments_path = BASE_DIR / "data" / "instruments.json"
with open(instruments_path, "r") as f:
    instrument_list = json.load(f)

print(f"Loaded {len(instrument_list)} instruments")

# ─── Watchlist ────────────────────────────────────────────────────────────────
WATCHLIST = [
    "ABB", "ACC", "ADANIENT", "ADANIPORTS", "ADANIGREEN", "ABCAPITAL", "ABFRL", "ALKEM",
    "AMBUJACEM", "ANGELONE", "APOLLOHOSP", "ASHOKLEY", "ASIANPAINT", "ASTRAL", "AUBANK",
    "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BALKRISIND",
    "BALRAMCHIN", "BANDHANBNK", "BANKBARODA", "BANKINDIA", "BATAINDIA", "BEL", "BERGEPAINT",
    "BHARATFORG", "BHEL", "BHARTIARTL", "BIOCON", "BRITANNIA", "BSOFT", "CANBK", "CANFINHOME",
    "CDSL", "CHAMBLFERT", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CONCOR",
    "COROMANDEL", "CROMPTON", "CUB", "CUMMINSIND", "CYIENT", "DABUR", "DALBHARAT", "DEEPAKNTR",
    "DELHIVERY", "DIVISLAB", "DIXON", "DLF", "DMART", "DRREDDY", "EICHERMOT", "ESCORTS",
    "FEDERALBNK", "GAIL", "GLENMARK", "GMRINFRA", "GNFC", "GODREJCP", "GRASIM", "GUJGASLTD",
    "HAVELLS", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR",
    "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDEA", "IDFC", "IDFCFIRSTB", "INDHOTEL", "INDIGO",
    "INDUSINDBK", "INDUSTOWER", "INFY", "IOC", "IPCALAB", "IRCTC", "ITC", "JINDALSTEL",
    "JKCEMENT", "JSWSTEEL", "JUBLFOOD", "KOTAKBANK", "L&TFH", "LT", "LTIM", "LUPIN", "M&M",
    "M&MFIN", "MANAPPURAM", "MARICO", "MARUTI", "MCX", "METROPOLIS", "MFSL", "MGL", "MOTHERSON",
    "MPHASIS", "MRF", "MUTHOOTFIN", "NAM-INDIA", "NATIONALUM", "NAVINFLUOR", "NESTLEIND",
    "NMDC", "NTPC", "OBEROIRLTY", "OFSS", "ONGC", "PAGEIND", "PEL", "PERSISTENT", "PETRONET",
    "PFC", "PIDILITIND", "PIIND", "POLYCAB", "POWERGRID", "PVRINOX", "RAMCOCEM", "RBLBANK",
    "RECLTD", "RELIANCE", "SAIL", "SBICARD", "SBILIFE", "SBIN", "SHREECEM", "SIEMENS", "SRF",
    "SUNPHARMA", "SUNTV", "SYNGENE", "TATACHEM", "TATACOMM", "TATACONSUM", "TATAELXSI",
    "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", "TECHM", "TORNTPHARM", "TRENT", "TVSMOTOR",
    "UBL", "ULTRACEMCO", "UPL", "VEDL", "VOLTAS", "WIPRO", "ZEEL", "ZYDUSLIFE"
]


# ─── Helpers ──────────────────────────────────────────────────────────────────
def token_lookup(ticker, instrument_list, exchange="NSE"):
    for instrument in instrument_list:
        if (instrument["name"] == ticker
                and instrument["exch_seg"] == exchange
                and instrument["symbol"].split('-')[-1] == "EQ"):
            return instrument["token"]


def symbol_lookup(token, instrument_list, exchange="NSE"):
    for instrument in instrument_list:
        if (instrument["token"] == token
                and instrument["exch_seg"] == exchange
                and instrument["symbol"].split('-')[-1] == "EQ"):
            return instrument["name"]


# ─── Generic candle fetcher ───────────────────────────────────────────────────
def hist_data(tickers, duration_days, interval, instrument_list, exchange="NSE"):
    """
    Fetch historical OHLC candles for a list of tickers.

    Parameters
    ----------
    tickers       : list of NSE symbol strings
    duration_days : how many calendar days back to request
    interval      : Angel One interval string e.g. ONE_DAY, ONE_HOUR
    instrument_list: loaded instruments.json
    exchange      : default NSE
    """
    result = {}
    for ticker in tickers:
        token = token_lookup(ticker, instrument_list, exchange)
        if token is None:
            print(f"Token not found for {ticker}")
            continue

        params = {
            "exchange": exchange,
            "symboltoken": token,
            "interval": interval,
            "fromdate": (dt.datetime.now() - dt.timedelta(days=duration_days)).strftime("%Y-%m-%d 09:15"),
            "todate":   dt.datetime.now().strftime("%Y-%m-%d 15:30")
        }

        print(f"Fetching {ticker} [{interval}]")
        response = None

        for attempt in range(3):
            try:
                time.sleep(3)
                response = obj.getCandleData(params)
                if response and response.get("status"):
                    print(f"  OK: {ticker}")
                    break
            except Exception as e:
                print(f"  {ticker} attempt {attempt + 1}: {e}")
                time.sleep(3)

        if not response or not response.get("status"):
            print(f"  Skipping {ticker}")
            continue

        df = pd.DataFrame(
            response["data"],
            columns=["date", "open", "high", "low", "close", "volume"]
        )
        df.set_index("date", inplace=True)
        result[ticker] = df

    return result


# ─── CPR calculation ──────────────────────────────────────────────────────────
def calculate_cpr(df):
    last_day = df.iloc[-1]
    high  = last_day["high"]
    low   = last_day["low"]
    close = last_day["close"]

    pivot  = (high + low + close) / 3
    raw_bc = (high + low) / 2
    raw_tc = (2 * pivot) - raw_bc
    bc     = min(raw_bc, raw_tc)
    tc     = max(raw_bc, raw_tc)
    width  = tc - bc
    cpr_percent = (width / pivot) * 100

    return {
        "pivot":       round(float(pivot), 2),
        "bc":          round(float(bc), 2),
        "tc":          round(float(tc), 2),
        "width":       round(float(width), 2),
        "cpr_percent": round(float(cpr_percent), 4)
    }


# ─── EMA calculation (1H timeframe) ──────────────────────────────────────────
def calculate_ema(df, periods=(20, 50, 100)):
    """
    Compute EMAs on the close price of a DataFrame of 1H candles.
    Returns a dict with ema_20, ema_50, ema_100 (latest values).
    Requires at least `max(periods)` candles — fetch 60 days of 1H data.
    """
    close = df["close"].astype(float)
    result = {}
    for p in periods:
        ema_series = close.ewm(span=p, adjust=False).mean()
        result[f"ema_{p}"] = round(float(ema_series.iloc[-1]), 2)
    return result


def get_ema_status(ltp, ema_value):
    """Return ABOVE or BELOW based on LTP vs EMA."""
    return "ABOVE" if ltp > ema_value else "BELOW"


# ─── Live data helpers ────────────────────────────────────────────────────────
def get_ltp(symbol, instrument_list):
    token = token_lookup(symbol, instrument_list)
    response = obj.ltpData("NSE", symbol, token)
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
    exchangeTokens = {"NSE": [token]}
    response = obj.getMarketData("FULL", exchangeTokens)
    data = response["data"]["fetched"][0]
    return data["totBuyQuan"], data["totSellQuan"]


# ─── State persistence ────────────────────────────────────────────────────────
def load_previous_state():
    state_file = BASE_DIR / "data" / "cpr_state.json"
    if not state_file.exists():
        return {}
    with open(state_file, "r") as f:
        return json.load(f)


def save_current_state(state):
    state_file = BASE_DIR / "data" / "cpr_state.json"
    with open(state_file, "w") as f:
        json.dump(state, f, indent=4)


def detect_status_changes(results_df):
    previous_state = load_previous_state()
    alerts = []
    current_state = {}

    for _, row in results_df.iterrows():
        symbol         = row["symbol"]
        current_status = row["cpr_status"]
        current_state[symbol] = current_status
        previous_status = previous_state.get(symbol)

        if previous_status is not None and previous_status != current_status:
            alerts.append({
                "symbol":     symbol,
                "old_status": previous_status,
                "new_status": current_status,
                "ltp":        row["ltp"]
            })

    save_current_state(current_state)
    return alerts


# ─── Main scanner ─────────────────────────────────────────────────────────────
print("\n=== Fetching daily candles for CPR calculation ===")
# Daily candles — last 3 days is enough for previous session OHLC
candle_data_daily = hist_data(WATCHLIST, 3, "ONE_DAY", instrument_list)

print("\n=== Fetching 1H candles for EMA calculation ===")
# 1H candles — need 100+ candles for EMA-100.
# NSE trades ~6.25 hours/day × 30 days ≈ 187 hourly candles → fetch 60 days to be safe
candle_data_1h = hist_data(WATCHLIST, 60, "ONE_HOUR", instrument_list)

results = []

for symbol in candle_data_daily:
    try:
        # ── CPR ──────────────────────────────────────────────────────────────
        cpr                  = calculate_cpr(candle_data_daily[symbol])
        ltp                  = get_ltp(symbol, instrument_list)
        buy_qty, sell_qty    = get_market_depth(symbol, instrument_list)
        cpr_status           = get_cpr_status(ltp, cpr["bc"], cpr["tc"])

        # ── EMA (1H) ─────────────────────────────────────────────────────────
        ema_values = {"ema_20": None, "ema_50": None, "ema_100": None}
        ema_status = {"ema20_status": "N/A", "ema50_status": "N/A", "ema100_status": "N/A"}

        if symbol in candle_data_1h:
            df_1h = candle_data_1h[symbol]
            if len(df_1h) >= 20:   # minimum bars needed
                ema_values = calculate_ema(df_1h)
                ema_status = {
                    "ema20_status":  get_ema_status(ltp, ema_values["ema_20"]),
                    "ema50_status":  get_ema_status(ltp, ema_values["ema_50"])  if len(df_1h) >= 50  else "N/A",
                    "ema100_status": get_ema_status(ltp, ema_values["ema_100"]) if len(df_1h) >= 100 else "N/A",
                }
        else:
            print(f"  No 1H data for {symbol} — EMA skipped")

        results.append({
            "symbol":       symbol,
            # CPR columns
            "pivot":        cpr["pivot"],
            "bc":           cpr["bc"],
            "tc":           cpr["tc"],
            "width":        cpr["width"],
            "cpr_percent":  cpr["cpr_percent"],
            # Live data
            "ltp":          ltp,
            "buy_qty":      buy_qty,
            "sell_qty":     sell_qty,
            "cpr_status":   cpr_status,
            # EMA values (1H)
            "ema_20":       ema_values["ema_20"],
            "ema_50":       ema_values["ema_50"],
            "ema_100":      ema_values["ema_100"],
            # EMA status (ABOVE / BELOW)
            "ema20_status":  ema_status["ema20_status"],
            "ema50_status":  ema_status["ema50_status"],
            "ema100_status": ema_status["ema100_status"],
        })

    except Exception as e:
        print(f"Error processing {symbol}: {e}")
        continue

results_df = pd.DataFrame(results)
results_df = results_df.sort_values(by="cpr_percent", ascending=True)
results_df.reset_index(drop=True, inplace=True)
results_df["narrow_cpr"] = (results_df["cpr_percent"] < 0.1)


def run_scanner():
    return results_df
