import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))  # allow `import src`
from src.db import get_engine  # noqa: E402

MASTER_CSV=Path("data/processed/olist_master.csv")
TABLE_NAME="olist_master"

DATE_COLS=[
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

def main():
    if not MASTER_CSV.exists():
        raise FileNotFoundError(
            f"{MASTER_CSV} not found. run pipeline/01_clean.py first."
        )

    print(f"Reading {MASTER_CSV} ...")
    df=pd.read_csv(MASTER_CSV,parse_dates=DATE_COLS)
    print(f"Loaded {len(df):,} rows, {len(df.columns)} columns")

    engine=get_engine()
    print(f"Writing to supabase table '{TABLE_NAME}' (if exists='replace') ...")
    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False ,
        chunksize=1000,
        method="multi"
    )

    with engine.connect() as conn:
        result=conn.exec_driver_sql(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        row_count=result.scalar()

    print(f"Done. Supabase '{TABLE_NAME}' now has {row_count:,} rows.")
    if row_count !=len(df):
        print("WARNING: row count mismatch between CSV and Supabase table!")

if __name__=="__main__":
    main()