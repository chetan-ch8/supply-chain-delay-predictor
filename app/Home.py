import sys
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))  # allow `import src`
from src.db import run_query  # noqa: E402

st.set_page_config(
    page_title="Supply Chain Delay Predictor",
    page_icon="📦",
    layout="wide",
)

@st.cache_data(ttl=3600)
def load_state_kpis() -> pd.DataFrame:
    return run_query("ontime_rate_by_state.sql")

@st.cache_data(ttl=3600)
def load_monthly_trend() -> pd.DataFrame:
    return run_query("monthly_delay_trend.sql")

def main():
    st.title("📦 Supply Chain Delay Predictor")
    st.caption(
        "Predicting late deliveries in Brazilian e-commerce — "
        "[Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), "
        "100k+ real orders."
    )

    try:
        state_df = load_state_kpis()
        trend_df = load_monthly_trend()
    except RuntimeError as e:
        st.error(f"Couldn't connect to the database: {e}")
        st.stop()

    if state_df.empty or trend_df.empty:
        st.warning("No data returned. Has the pipeline been run (`make pipeline`)?")
        st.stop()

    total_orders = int(state_df["total_orders"].sum())
    total_late = int(state_df["late_orders"].sum())
    overall_on_time_pct = round(100 * (1 - total_late / total_orders), 1)
    avg_delay = round(
        (state_df["avg_delay_days"] * state_df["total_orders"]).sum() / total_orders, 1
    )
    worst_state_row = state_df.sort_values("on_time_rate_pct").iloc[0]
    worst_state = worst_state_row["customer_state"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall On-Time Rate", f"{overall_on_time_pct}%")
    col2.metric("Avg Delivery Delay", f"{avg_delay} days")
    col3.metric("Worst-Performing State", worst_state,
                f"{worst_state_row['on_time_rate_pct']}% on-time")
    col4.metric("Total Orders Analyzed", f"{total_orders:,}")

    st.divider()

    st.subheader("Monthly On-Time Rate Trend")
    trend_df["month"] = pd.to_datetime(trend_df["month"])
    chart_df = trend_df.set_index("month")[["late_rate_pct"]].rename(
        columns={"late_rate_pct": "Late rate (%)"}
    )
    chart_df["On-time rate (%)"] = 100 - chart_df["Late rate (%)"]
    st.line_chart(chart_df[["On-time rate (%)"]])

    with st.expander("View raw monthly data"):
        st.dataframe(trend_df, use_container_width=True)

    st.divider()
    st.caption(
        "Live link: add your deployed Streamlit Cloud URL to the README once deployed. "
        "See the Explorer, Risk Predictor, and AI Insights pages in the sidebar."
    )

if __name__ == "__main__":
    main()