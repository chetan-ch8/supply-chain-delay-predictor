from pathlib import Path
import pandas as pd
import pytest

MASTER_CSV = Path("data/processed/olist_master.csv")

@pytest.fixture(scope="module")
def master_df():
    if not MASTER_CSV.exists():
        pytest.skip(f"{MASTER_CSV} not found — run pipeline/01_clean.py first")
    return pd.read_csv(MASTER_CSV, parse_dates=[
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ])

def test_file_not_empty(master_df):
    assert len(master_df) > 1000, "olist_master.csv looks suspiciously small"

def test_no_nulls_in_critical_columns(master_df):
    critical = [
        "order_id", "seller_id", "product_id",
        "delivery_delay_days", "is_late", "distance_km",
        "product_category_name_english", "seller_state", "customer_state",
    ]
    nulls = master_df[critical].isnull().sum()
    assert nulls.sum() == 0, f"Found nulls in critical columns:\n{nulls[nulls > 0]}"

def test_is_late_is_binary(master_df):
    assert set(master_df["is_late"].unique()).issubset({0, 1}), \
        "is_late should only contain 0 or 1"

def test_delivery_delay_days_is_numeric_and_consistent_with_is_late(master_df):
    assert pd.api.types.is_numeric_dtype(master_df["delivery_delay_days"])
    # is_late must be a strict re-encoding of delivery_delay_days > 0
    recomputed = (master_df["delivery_delay_days"] > 0).astype(int)
    assert (recomputed == master_df["is_late"]).all(), \
        "is_late does not match sign of delivery_delay_days"

def test_distance_km_within_plausible_range(master_df):
    assert master_df["distance_km"].min() >= 0
    assert master_df["distance_km"].max() < 8000, \
        "distance_km exceeds the max plausible distance within Brazil"

def test_date_columns_are_datetime(master_df):
    date_cols = [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        assert pd.api.types.is_datetime64_any_dtype(master_df[col]), \
            f"{col} was not parsed as a datetime"

def test_price_and_freight_are_non_negative(master_df):
    for col in ["price", "freight_value"]:
        assert col in master_df.columns, f"{col} column missing from olist_master.csv"
        assert pd.api.types.is_numeric_dtype(master_df[col]), \
            f"{col} should be numeric"
        assert (master_df[col] >= 0).all(), \
            f"{col} contains negative values"