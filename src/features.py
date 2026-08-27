from pathlib import Path
import joblib
import numpy as np
import pandas as pd

ENCODER_PATH = Path("models/feature_encoder.pkl")
FEATURE_COLS = [
    "distance_km",
    "product_weight_g",
    "freight_value",
    "day_of_week",
    "seller_avg_delay_historical",
    "category_encoded",
    "state_encoded",
]

def load_encoder_bundle(path: Path = ENCODER_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run pipeline/03_features.py first to fit "
            "and save the encoders."
        )
    return joblib.load(path)

def build_features(df: pd.DataFrame, encoder_bundle: dict | None = None) -> pd.DataFrame:
    if encoder_bundle is None:
        encoder_bundle = load_encoder_bundle()

    category_encoder = encoder_bundle["category_encoder"]
    state_encoder = encoder_bundle["state_encoder"]
    seller_lookup = encoder_bundle["seller_avg_delay_lookup"]
    global_mean_delay = encoder_bundle["global_mean_delay"]

    df = df.copy()
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["day_of_week"] = df["order_purchase_timestamp"].dt.dayofweek

    df["seller_avg_delay_historical"] = df["seller_id"].map(seller_lookup).fillna(
        global_mean_delay
    )

    df["category_encoded"] = _safe_transform(
        category_encoder, df["product_category_name_english"]
    )
    df["state_encoded"] = _safe_transform(state_encoder, df["customer_state"])

    return df[FEATURE_COLS]

def build_single_order(order: dict, encoder_bundle: dict | None = None) -> pd.DataFrame:
    if encoder_bundle is None:
        encoder_bundle = load_encoder_bundle()

    category_encoder = encoder_bundle["category_encoder"]
    state_encoder = encoder_bundle["state_encoder"]
    seller_lookup = encoder_bundle["seller_avg_delay_lookup"]
    global_mean_delay = encoder_bundle["global_mean_delay"]

    if "day_of_week" in order:
        day_of_week = order["day_of_week"]
    else:
        day_of_week = pd.to_datetime(order["order_purchase_timestamp"]).dayofweek

    seller_avg_delay = seller_lookup.get(order.get("seller_id"), global_mean_delay)

    category_encoded = _safe_transform(
        category_encoder, pd.Series([order["product_category_name_english"]])
    )[0]
    state_encoded = _safe_transform(
        state_encoder, pd.Series([order["customer_state"]])
    )[0]

    row = {
        "distance_km": order["distance_km"],
        "product_weight_g": order["product_weight_g"],
        "freight_value": order["freight_value"],
        "day_of_week": day_of_week,
        "seller_avg_delay_historical": seller_avg_delay,
        "category_encoded": category_encoded,
        "state_encoded": state_encoded,
    }
    return pd.DataFrame([row])[FEATURE_COLS]

def _safe_transform(encoder, series: pd.Series):
    """LabelEncoder.transform, but unseen labels map to -1 instead of raising."""
    known = set(encoder.classes_)
    values = series.to_numpy()
    is_known = pd.Series(values).isin(known).to_numpy()

    result = np.full(len(values), -1, dtype=int)
    if is_known.any():
        result[is_known] = encoder.transform(values[is_known])
    return result