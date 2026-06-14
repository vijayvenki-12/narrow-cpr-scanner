import streamlit as st
from streamlit_autorefresh import st_autorefresh
from scanner import run_scanner, detect_status_changes
from io import BytesIO
from datetime import datetime
import pandas as pd

# ─── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(page_title="Narrow CPR Scanner", layout="wide")

# ─── Auto-refresh every 5 minutes ────────────────────────────────────────────
st_autorefresh(interval=300 * 1000, key="scanner_refresh")

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("📊 Narrow CPR Scanner")
st.caption(f"Last Refresh: {datetime.now().strftime('%H:%M:%S')}  |  1H EMA: 20 / 50 / 100")

# ─── Run scanner ─────────────────────────────────────────────────────────────
df = run_scanner()

# ─── CPR transition alerts ───────────────────────────────────────────────────
alerts = detect_status_changes(df)
for alert in alerts:
    st.warning(
        f"⚠️ **{alert['symbol']}** moved from **{alert['old_status']}** "
        f"to **{alert['new_status']}** at LTP {alert['ltp']}"
    )

# ─── Display copy (narrow_cpr as emoji) ──────────────────────────────────────
display_df = df.copy()
display_df["narrow_cpr"] = display_df["narrow_cpr"].map(lambda x: "✅" if x else "")

# ─── Styling ─────────────────────────────────────────────────────────────────
def color_cpr_status(val):
    """Colour the cpr_status column."""
    if val == "ABOVE_CPR":
        return "background-color: #006400; color: white"   # dark green
    elif val == "BELOW_CPR":
        return "background-color: #8B0000; color: white"   # dark red
    elif val == "INSIDE_CPR":
        return "background-color: #B8860B; color: white"   # dark amber
    return ""


def color_ema_status(val):
    """
    Colour EMA status columns.
    ABOVE = soft green  |  BELOW = soft red  |  N/A = neutral
    """
    if val == "ABOVE":
        return "background-color: #228B22; color: white"   # forest green
    elif val == "BELOW":
        return "background-color: #B22222; color: white"   # firebrick red
    return ""                                              # N/A — no colour


styled_df = (
    display_df.style
    .map(color_cpr_status,  subset=["cpr_status"])
    .map(color_ema_status,  subset=["ema20_status", "ema50_status", "ema100_status"])
)

st.dataframe(styled_df, use_container_width=True)

# ─── Legend ──────────────────────────────────────────────────────────────────
with st.expander("ℹ️ Column Legend", expanded=False):
    st.markdown("""
| Column | Description |
|---|---|
| `pivot` | Previous session pivot: (H+L+C)/3 |
| `bc` / `tc` | Bottom and Top CPR levels |
| `cpr_percent` | CPR width as % of pivot — lower = narrower |
| `narrow_cpr` | ✅ if cpr_percent < 0.1% |
| `ltp` | Live last traded price |
| `buy_qty` / `sell_qty` | Total market depth quantities |
| `cpr_status` | 🟢 ABOVE_CPR / 🔴 BELOW_CPR / 🟡 INSIDE_CPR |
| `ema_20` / `ema_50` / `ema_100` | 1H EMA values (last completed candle) |
| `ema20_status` | ABOVE/BELOW LTP vs 1H 20 EMA |
| `ema50_status` | ABOVE/BELOW LTP vs 1H 50 EMA |
| `ema100_status` | ABOVE/BELOW LTP vs 1H 100 EMA |
    """)

# ─── Excel download ───────────────────────────────────────────────────────────
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Narrow_CPR")
    return output.getvalue()

excel_data = to_excel(display_df)

st.download_button(
    label="📥 Download Excel",
    data=excel_data,
    file_name="narrow_cpr_scan.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
