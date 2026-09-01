
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.db import run_query  # noqa: E402

st.set_page_config(page_title="Explorer — Supply Chain Delay Predictor", page_icon="🔎", layout="wide")


@st.cache_data(ttl=3600)
def load_state_data() -> pd.DataFrame:
    return run_query("ontime_rate_by_state.sql")


@st.cache_data(ttl=3600)
def load_category_data() -> pd.DataFrame:
    return run_query("delay_by_category.sql")


def main():
    st.title("🔎 Explorer")
    st.caption("Filter and drill into on-time performance by state and category.")

    try:
        state_df = load_state_data()
        category_df = load_category_data()
    except RuntimeError as e:
        st.error(f"Couldn't connect to the database: {e}")
        st.stop()

    if state_df.empty or category_df.empty:
        st.warning("No data returned. Has the pipeline been run (`make pipeline`)?")
        st.stop()

    # --- filters ---
    col1, col2 = st.columns([2, 1])
    with col1:
        all_states = sorted(state_df["customer_state"].unique())
        selected_states = st.multiselect(
            "Filter by customer state", options=all_states, default=all_states
        )
    with col2:
        max_possible = int(state_df["total_orders"].max())
        min_orders = st.slider(
            "Minimum order count", min_value=0, max_value=max_possible,
            value=0, step=max(1, max_possible // 20),
        )

    filtered_state_df = state_df[
        state_df["customer_state"].isin(selected_states)
        & (state_df["total_orders"] >= min_orders)
    ].sort_values("on_time_rate_pct")

    st.subheader("On-Time Rate by State")
    if filtered_state_df.empty:
        st.info("No states match the current filters.")
    else:
        st.bar_chart(
            filtered_state_df.set_index("customer_state")["on_time_rate_pct"],
            use_container_width=True,
        )
        st.dataframe(filtered_state_df, use_container_width=True)

    st.divider()

    st.subheader("Average Delay by Product Category")
    top_n = st.slider("Show top N categories by avg delay", 5, min(30, len(category_df)), 15)
    top_categories = category_df.head(top_n)
    st.bar_chart(
        top_categories.set_index("category")["avg_delay_days"],
        use_container_width=True,
    )
    st.dataframe(top_categories, use_container_width=True)

if __name__ == "__main__":
    main()