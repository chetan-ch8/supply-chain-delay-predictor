from pathlib import Path
import pandas as pd

IN_PATH = Path("data/processed/olist_master.csv")
OUT_DIR = Path("data/exports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def build_by_state(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("customer_state")
        .agg(
            total_orders=("order_id", "count"),
            late_orders=("is_late", "sum"),
            avg_delay_days=("delivery_delay_days", "mean"),
        )
        .reset_index()
    )
    out["on_time_rate_pct"] = (100 * (1 - out["late_orders"] / out["total_orders"])).round(2)
    out["avg_delay_days"] = out["avg_delay_days"].round(2)
    return out.sort_values("on_time_rate_pct").reset_index(drop=True)

def build_by_category(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.groupby("product_category_name_english")
        .agg(
            total_orders=("order_id", "count"),
            avg_delay_days=("delivery_delay_days", "mean"),
            late_rate_pct=("is_late", "mean"),
        )
        .reset_index()
        .rename(columns={"product_category_name_english": "category"})
    )
    out = out[out["total_orders"] >= 30]  # drop tiny categories — noisy averages
    out["avg_delay_days"] = out["avg_delay_days"].round(2)
    out["late_rate_pct"] = (100 * out["late_rate_pct"]).round(2)
    return out.sort_values("avg_delay_days", ascending=False).reset_index(drop=True)

def build_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    out = (
        df.set_index("order_purchase_timestamp")
        .resample("MS")
        .agg(total_orders=("order_id", "count"), late_rate=("is_late", "mean"),
             avg_delay_days=("delivery_delay_days", "mean"))
        .reset_index()
        .rename(columns={"order_purchase_timestamp": "month"})
    )
    out["late_rate_pct"] = (100 * out["late_rate"]).round(2)
    out["avg_delay_days"] = out["avg_delay_days"].round(2)
    out = out.drop(columns=["late_rate"])
    return out

def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"{IN_PATH} not found. Run pipeline/01_clean.py first.")

    df = pd.read_csv(IN_PATH, parse_dates=["order_purchase_timestamp"])

    exports = {
        "by_state.csv": build_by_state(df),
        "by_category.csv": build_by_category(df),
        "monthly_trend.csv": build_monthly_trend(df),
    }

    for filename, out_df in exports.items():
        path = OUT_DIR / filename
        out_df.to_csv(path, index=False)
        print(f"Saved -> {path}  shape={out_df.shape}")

if __name__ == "__main__":
    main()