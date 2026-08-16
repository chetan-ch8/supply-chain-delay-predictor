import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()


def _get_secret(key: str) -> str | None:
    try:
        import streamlit as st  # imported lazily — pipeline scripts don't need Streamlit at all
        if key in st.secrets:
            return st.secrets[key]
    except (ImportError, FileNotFoundError):
        # ImportError: streamlit not installed (fine — plain scripts, tests, notebooks)
        # FileNotFoundError: streamlit is installed but no secrets.toml exists locally (fine)
        pass
    except Exception:
        # st.secrets can raise other errors when no secrets file/context exists at all
        pass

    return os.getenv(key)

def get_db_url() -> str:
    url = _get_secret("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Locally: copy .env.example to .env and "
            "fill in your Supabase connection string (Project Settings -> "
            "Database -> Connection string -> URI). On Streamlit Cloud: add "
            "DATABASE_URL under your app's Settings -> Secrets."
        )
    return url

def get_engine() -> Engine:
    return create_engine(get_db_url(), pool_pre_ping=True)

def run_query(sql_file: str, params: dict | None = None) -> pd.DataFrame:
    sql_path = Path("sql") / sql_file
    if not sql_path.exists():
        raise FileNotFoundError(f"No such SQL file: {sql_path}")

    query = sql_path.read_text()
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})


def test_connection() -> bool:
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True


if __name__ == "__main__":
    ok = test_connection()
    print("Supabase connection OK" if ok else "Supabase connection FAILED")
