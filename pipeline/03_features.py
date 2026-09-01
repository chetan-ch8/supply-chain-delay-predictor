from pathlib import Path
import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder

IN_PATH = Path("data/processed/olist_master.csv")
OUT_PATH = Path("data/processed/model_features.csv")
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

FEATURE_COLS = [
    "distance_km",
    "product_weight_g",
    "freight_value",
    "day_of_week",
    "seller_avg_delay_historical",
    "category_encoded",
    "state_encoded",
]
TARGET_COLS = ["delivery_delay_days", "is_late"]

def add_seller_historical_avg(df: pd.DataFrame)->pd.DataFrame:
    df = df.sort_values("order_purchase_timestamp").reset_index(drop=True)

    global_mean_delay = df["delivery_delay_days"].mean()

    df["seller_avg_delay_historical"] = (
        df.groupby("seller_id")["delivery_delay_days"]
        .apply(lambda s: s.expanding().mean().shift(1))
        .reset_index(level=0, drop=True)
    )
    df["seller_avg_delay_historical"] = df["seller_avg_delay_historical"].fillna(
        global_mean_delay
    )
    return df, global_mean_delay

def build_seller_lookup(df: pd.DataFrame) -> dict:
    latest = (
        df.sort_values("order_purchase_timestamp")
        .groupby("seller_id")["seller_avg_delay_historical"]
        .last()
    )
    return latest.to_dict()

def main():
    print(f"Reading {IN_PATH} ...")
    df = pd.read_csv(IN_PATH, parse_dates=["order_purchase_timestamp"])

    df["day_of_week"] = df["order_purchase_timestamp"].dt.dayofweek

    df, global_mean_delay = add_seller_historical_avg(df)

    category_encoder = LabelEncoder()
    df["category_encoded"] = category_encoder.fit_transform(
        df["product_category_name_english"]
    )

    state_encoder = LabelEncoder()
    df["state_encoded"] = state_encoder.fit_transform(df["customer_state"])

    seller_lookup = build_seller_lookup(df)

    model_df = df[FEATURE_COLS + TARGET_COLS].copy()

    n_before = len(model_df)
    model_df = model_df.dropna()
    n_after = len(model_df)
    if n_after < n_before:
        print(f"Dropped {n_before - n_after} rows with null features/targets")

    assert model_df.isnull().sum().sum() == 0, "model_features.csv still has nulls!"

    model_df.to_csv(OUT_PATH, index=False)
    print(f"Saved -> {OUT_PATH}  ({len(model_df):,} rows, "
          f"{len(FEATURE_COLS)} features + {len(TARGET_COLS)} targets)")

    encoder_bundle = {
        "category_encoder": category_encoder,
        "state_encoder": state_encoder,
        "seller_avg_delay_lookup": seller_lookup,
        "global_mean_delay": global_mean_delay,
        "feature_cols": FEATURE_COLS,
    }
    encoder_path = MODELS_DIR / "feature_encoder.pkl"
    joblib.dump(encoder_bundle, encoder_path)
    print(f"Saved -> {encoder_path}")

if __name__ == "__main__":
    main()