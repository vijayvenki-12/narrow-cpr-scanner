import streamlit as st
from scanner import run_scanner, detect_status_changes
from streamlit_autorefresh import st_autorefresh
from io import BytesIO
import pandas as pd

st_autorefresh(
    interval=300 * 1000,
    key="scanner_refresh"
)
from datetime import datetime

st.write(
    f"Last Refresh: {datetime.now().strftime('%H:%M:%S')}"
)
st.set_page_config(
    page_title="Narrow CPR Scanner",
    layout="wide"
)

st.title("Narrow CPR Scanner")

df = run_scanner()

alerts = detect_status_changes(df)

for alert in alerts:

    st.warning(
        f"{alert['symbol']} moved "
        f"from {alert['old_status']} "
        f"to {alert['new_status']} "
        f"at LTP {alert['ltp']}"
    )
def color_status(val):

    if val == "ABOVE_CPR":
        return "background-color: #006400; color: white"   # Dark Green

    elif val == "BELOW_CPR":
        return "background-color: #8B0000; color: white"   # Dark Red

    elif val == "INSIDE_CPR":
        return "background-color: #B8860B; color: white"   # Dark Yellow

    return ""


styled_df = df.style.map(
    color_status,
    subset=["cpr_status"]
)
df["narrow_cpr"] = df["narrow_cpr"].map(
    lambda x: "✅" if x else ""
)
st.dataframe(
    styled_df,
    use_container_width=True
)

def to_excel(df):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Narrow_CPR"
        )

    return output.getvalue()

excel_data = to_excel(df)

st.download_button(
    label="📥 Download Excel",
    data=excel_data,
    file_name="narrow_cpr_scan.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)