
import sys
from datetime import date
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.models import load_models, predict_delay  # noqa: E402

st.set_page_config(page_title="Risk Predictor — Supply Chain Delay Predictor", page_icon="🎯", layout="wide")

RISK_COLORS = {
    "low": ("🟢", "#1a7f37", "Low risk — this order is likely to arrive on time."),
    "medium": ("🟡", "#9a6700", "Medium risk — worth keeping an eye on."),
    "high": ("🔴", "#cf222e", "High risk — this order is likely to be late."),
}

# Sensible defaults so the form is useful with zero input
DEFAULTS = {
    "distance_km": 500.0,
    "product_weight_g": 1000.0,
    "freight_value": 25.0,
    "purchase_date": date.today(),
    "seller_id": "",
    "category": "toys_en",
    "state": "SP",
}

BR_STATES = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
]


@st.cache_resource
def get_cached_models():
    return load_models()


def main():
    st.title("🎯 Risk Predictor")
    st.caption("Estimate delivery delay risk for a new order.")

    try:
        models = get_cached_models()
    except FileNotFoundError as e:
        st.error(f"Models not available: {e}")
        st.stop()

    with st.form("risk_predictor_form"):
        col1, col2 = st.columns(2)

        with col1:
            distance_km = st.number_input(
                "Distance (km)", min_value=0.0, value=DEFAULTS["distance_km"], step=10.0
            )
            product_weight_g = st.number_input(
                "Product weight (g)", min_value=1.0, value=DEFAULTS["product_weight_g"], step=50.0
            )
            freight_value = st.number_input(
                "Freight value (R$)", min_value=0.0, value=DEFAULTS["freight_value"], step=1.0
            )
            purchase_date = st.date_input("Order purchase date", value=DEFAULTS["purchase_date"])

        with col2:
            seller_id = st.text_input(
                "Seller ID (optional — leave blank if unknown)",
                value=DEFAULTS["seller_id"],
                help="If this seller exists in the training data, their historical "
                     "average delay is used as a feature. Unknown/blank falls back "
                     "to the global average.",
            )
            category = st.text_input(
                "Product category (English name)", value=DEFAULTS["category"],
                help="e.g. toys_en, electronics_en, furniture_en — matches "
                     "product_category_name_english from training data.",
            )
            state = st.selectbox("Customer state", options=BR_STATES,
                                  index=BR_STATES.index(DEFAULTS["state"]))

        submitted = st.form_submit_button("Predict delay risk", use_container_width=True)

    if submitted:
        order = {
            "distance_km": distance_km,
            "product_weight_g": product_weight_g,
            "freight_value": freight_value,
            "order_purchase_timestamp": str(purchase_date),
            "seller_id": seller_id or "unknown_seller",
            "product_category_name_english": category,
            "customer_state": state,
        }

        result = predict_delay(order, models=models)

        icon, color, message = RISK_COLORS[result["risk_level"]]

        st.markdown(
            f"""
            <div style="padding: 1.25rem; border-radius: 0.5rem;
                        border: 2px solid {color}; background-color: {color}15;">
                <h3 style="margin: 0; color: {color};">{icon} {result['risk_level'].upper()} RISK</h3>
                <p style="margin: 0.5rem 0 0 0;">{message}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        col1, col2 = st.columns(2)
        col1.metric("Predicted delay", f"{result['delay_days']} days",
                     help="Negative = predicted to arrive before the estimate.")
        col2.metric("Probability of being late", f"{result['is_late_probability'] * 100:.1f}%")


if __name__ == "__main__":
    main()
