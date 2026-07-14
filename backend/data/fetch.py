from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.data.cache import save_price_frame


def _clean_price_frame(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if raw.empty:
        raise ValueError(f"No data returned for ticker: {ticker}")

    if isinstance(raw.columns, pd.MultiIndex):
        raw = raw.copy()
        raw.columns = raw.columns.get_level_values(0)

    if "Close" not in raw.columns:
        raise ValueError(f"Expected a Close column for ticker: {ticker}")

    available_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in raw.columns]
    data = raw[available_cols].copy()
    data = data.reset_index()
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        data = data.dropna(subset=["Date"])
        data = data.set_index("Date")
    else:
        data.index = pd.to_datetime(data.index, errors="coerce")
        data = data.dropna()

    data = data.sort_index()
    data.index.name = "Date"
    return data


def fetch_history(tickers: Iterable[str], period: str = "5y", interval: str = "1d") -> dict[str, pd.DataFrame]:
    """Download historical OHLCV data for each ticker and return a dict of DataFrames."""
    results: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        raw = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
        results[ticker] = _clean_price_frame(raw, ticker)
    return results


def fetch_and_cache(tickers: Iterable[str], period: str = "5y", interval: str = "1d") -> list[str]:
    """Download and cache historical data for each ticker."""
    downloaded: list[str] = []
    for ticker in tickers:
        raw = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
        data = _clean_price_frame(raw, ticker)
        save_price_frame(ticker, data)
        downloaded.append(ticker)
    return downloaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Download historical equity data and cache it locally")
    parser.add_argument("--tickers", nargs="+", required=True, help="Tickers to download, e.g. RELIANCE.NS ^NSEI ^INDIAVIX")
    parser.add_argument("--period", default="5y", help="yfinance period, e.g. 5y or 2y")
    parser.add_argument("--interval", default="1d", help="yfinance interval, e.g. 1d")
    args = parser.parse_args()

    downloaded = fetch_and_cache(args.tickers, period=args.period, interval=args.interval)
    print(f"Cached historical data for: {', '.join(downloaded)}")


if __name__ == "__main__":
    main()
