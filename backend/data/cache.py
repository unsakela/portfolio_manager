from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT_DIR / "data_cache"


def ticker_to_cache_key(ticker: str) -> str:
    """Return the normalized key used to store/retrieve a ticker in the price cache dict."""
    return ticker.replace('/', '_')


def ensure_cache_dir() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def save_price_frame(ticker: str, data: pd.DataFrame) -> Path:
    ensure_cache_dir()
    file_path = CACHE_DIR / f"{ticker.replace('/', '_')}.csv"
    data.to_csv(file_path)
    return file_path


def load_price_frame(ticker: str) -> pd.DataFrame:
    file_path = CACHE_DIR / f"{ticker.replace('/', '_')}.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Cache file not found for {ticker}: {file_path}")
    return pd.read_csv(file_path, index_col=0, parse_dates=True)


def list_cached_tickers() -> list[str]:
    if not CACHE_DIR.exists():
        return []
    return sorted([p.stem for p in CACHE_DIR.glob("*.csv")])


def load_all_cached_prices() -> Dict[str, pd.DataFrame]:
    cached = {}
    for ticker in list_cached_tickers():
        cached[ticker] = load_price_frame(ticker)
    return cached
