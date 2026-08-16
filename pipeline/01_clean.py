import numpy as np
import pandas as pd
from pathlib import Path

RAW=Path("data/raw")
OUT=Path("data/processed")
OUT.mkdir(parents=True,exist_ok=True)

DATE_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

def haversine_km(lat1,lon1,lat2,lon2):
    lat1,lon1,lat2,lon2=map(np.radians,[lat1,lon1,lat2,lon2])
    dlat=lat2-lat1
    dlon=lon2-lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371.0  # Earth radius in km
    return c * r



def load_raw():
    orders = pd.read_csv(RAW / "olist_orders_dataset.csv")
    items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    sellers = pd.read_csv(RAW / "olist_sellers_dataset.csv")
    customers = pd.read_csv(RAW / "olist_customers_dataset.csv")
    geoloc = pd.read_csv(RAW / "olist_geolocation_dataset.csv")
    category_translation = pd.read_csv(RAW / "product_category_name_translation.csv")
    return orders, items, products, sellers, customers, geoloc, category_translation

def build_geoloc_lookup(geoloc:pd.DataFrame)->pd.DataFrame:
    return(
        geoloc.groupby("geolocation_zip_code_prefix",as_index=False)
        .agg(
            lat=("geolocation_lat","mean"),
            lng=("geolocation_lng","mean"),
        )
    )

def merge_all(orders,items,products,sellers,customers,geoloc,category_translation):
    geoloc_lookup = build_geoloc_lookup(geoloc)
    items_agg=(
        items.groupby("order_id",as_index=False)
        .agg(
            product_id=("product_id", "first"),
            seller_id=("seller_id", "first"),
            price=("price", "sum"),
            freight_value=("freight_value", "sum"),
        )
    )
    df = orders.merge(items_agg, on="order_id", how="inner")
    df = df.merge(products, on="product_id", how="left")
    df = df.merge(category_translation, on="product_category_name", how="left")
    df = df.merge(sellers, on="seller_id", how="left")
    df = df.merge(customers, on="customer_id", how="left")

    df["seller_zip_code_prefix"] = df["seller_zip_code_prefix"].astype("Int64").astype(str)
    df["customer_zip_code_prefix"] = df["customer_zip_code_prefix"].astype("Int64").astype(str)
    geoloc_lookup["geolocation_zip_code_prefix"] = (
        geoloc_lookup["geolocation_zip_code_prefix"].astype("Int64").astype(str)
    )

    df = df.merge(
        geoloc_lookup.rename(columns={"lat": "seller_lat", "lng": "seller_lng"}),
        left_on="seller_zip_code_prefix",
        right_on="geolocation_zip_code_prefix",
        how="left",
    ).drop(columns=["geolocation_zip_code_prefix"])

    df = df.merge(
        geoloc_lookup.rename(columns={"lat": "customer_lat", "lng": "customer_lng"}),
        left_on="customer_zip_code_prefix",
        right_on="geolocation_zip_code_prefix",
        how="left",
    ).drop(columns=["geolocation_zip_code_prefix"])

    return df

def clean_and_engineer(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["order_status"] == "delivered"].copy()

    for col in DATE_COLS:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    required = [
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "order_purchase_timestamp",
        "seller_lat", "seller_lng", "customer_lat", "customer_lng",
        "seller_state", "customer_state",
        "product_category_name_english",
    ]
    df = df.dropna(subset=required).copy()

    df["delivery_delay_days"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400.0

    df["is_late"] = (df["delivery_delay_days"] > 0).astype(int)

    df["distance_km"] = haversine_km(
        df["seller_lat"], df["seller_lng"], df["customer_lat"], df["customer_lng"]
    )

    df["price"] = df["price"].astype(float)
    df["freight_value"] = df["freight_value"].astype(float)
    df["product_weight_g"] = df["product_weight_g"].astype(float)
    df["seller_state"] = df["seller_state"].astype(str)
    df["customer_state"] = df["customer_state"].astype(str)
    df["product_category_name_english"] = df["product_category_name_english"].astype(str)

    df = df[(df["distance_km"] >= 0) & (df["distance_km"] < 8000)]
    df = df[df["freight_value"] >= 0]
    df = df[df["product_weight_g"] > 0]

    keep_cols = [
        "order_id", "customer_id", "seller_id", "product_id",
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "price", "freight_value", "product_weight_g",
        "product_category_name_english",
        "seller_state", "customer_state",
        "distance_km", "delivery_delay_days", "is_late",
    ]
    return df[keep_cols].reset_index(drop=True)

def main():
    print("Loading raw CSVs from data/raw/ ...")
    orders, items, products, sellers, customers, geoloc, category_translation = load_raw()

    print("Merging tables ...")
    merged = merge_all(orders, items, products, sellers, customers, geoloc, category_translation)

    print(f"Rows after merge: {len(merged):,}")

    print("Cleaning + engineering features ...")
    master = clean_and_engineer(merged)

    print(f"Rows after cleaning: {len(master):,}")
    print(f"is_late rate: {master['is_late'].mean():.2%}")

    out_path = OUT / "olist_master.csv"
    master.to_csv(out_path, index=False)
    print(f"Saved -> {out_path}")
   
if __name__=="__main__":
    main()