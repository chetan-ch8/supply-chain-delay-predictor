
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.db import run_query  # noqa: E402
from src.insights import generate_insights  # noqa: E402

st.set_page_config(page_title="AI Insights — Supply Chain Delay Predictor", page_icon="🤖", layout="wide")


@st.cache_data(ttl=3600)
def load_kpis() -> dict:
    state_df = run_query("ontime_rate_by_state.sql")
    trend_df = run_query("monthly_delay_trend.sql")

    total_orders = int(state_df["total_orders"].sum())
    total_late = int(state_df["late_orders"].sum())
    overall_on_time_pct = round(100 * (1 - total_late / total_orders), 1)
    avg_delay = round(
        (state_df["avg_delay_days"] * state_df["total_orders"]).sum() / total_orders, 1
    )
    worst_state_row = state_df.sort_values("on_time_rate_pct").iloc[0]

    trend_sorted = trend_df.sort_values("month")
    if len(trend_sorted) >= 2:
        latest, previous = trend_sorted.iloc[-1], trend_sorted.iloc[-2]
        delta = round(latest["late_rate_pct"] - previous["late_rate_pct"], 1)
        trend_desc = f"{'up' if delta >= 0 else 'down'} {abs(delta)}pts vs previous month"
    else:
        trend_desc = "not enough history to compute a trend"

    return {
        "overall_on_time_pct": overall_on_time_pct,
        "avg_delay_days": avg_delay,
        "worst_state": worst_state_row["customer_state"],
        "worst_state_on_time_pct": worst_state_row["on_time_rate_pct"],
        "total_orders": total_orders,
        "late_rate_trend": trend_desc,
    }

def main():
    st.title("AI Insights")
    st.caption("Live KPIs, summarized into plain-English action items by Gemini.")

    try:
        kpis = load_kpis()
    except RuntimeError as e:
        st.error(f"Couldn't connect to the database: {e}")
        st.stop()

    with st.expander("View raw KPIs", expanded=False):
        st.json(kpis)

    if st.button("Generate insights", type="primary"):
        with st.spinner("Asking Gemini to summarize this week's KPIs..."):
            try:
                result = generate_insights(kpis)
            except RuntimeError as e:
                st.error(f"Couldn't generate insights: {e}")
                st.stop()
            except Exception as e:
                st.error(f"Gemini request failed: {e}")
                st.stop()

        st.subheader("Key Takeaways")
        for bullet in result["bullets"]:
            st.markdown(f"- {bullet}")

        if result.get("risk_flag"):
            is_none = result["risk_flag"].lower().startswith("none")
            if is_none:
                st.success(f"✅ {result['risk_flag']}")
            else:
                st.warning(f"⚠️ **RISK:** {result['risk_flag']}")


if __name__ == "__main__":
    main()
