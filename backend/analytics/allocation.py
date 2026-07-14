from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, Any

import pandas as pd


def _latest_close(price_frame: pd.DataFrame) -> float:
    if price_frame.empty:
        raise ValueError("Price data is empty")
    close = price_frame["Close"].dropna()
    if close.empty:
        raise ValueError("Close column has no usable values")
    return float(close.iloc[-1])


def compute_portfolio_allocation(
    holdings: Iterable[Mapping[str, Any]],
    price_cache: Mapping[str, pd.DataFrame],
    sector_map: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    """Compute current portfolio allocation by stock and by sector using latest cached prices."""
    sector_map = sector_map or {}
    by_stock: List[Dict[str, Any]] = []
    by_sector: Dict[str, float] = defaultdict(float)
    total_value = 0.0

    for holding in holdings:
        ticker = str(holding["ticker"])
        quantity = float(holding["quantity"])
        cache_key = ticker.replace('/', '_')
        if cache_key not in price_cache:
            raise KeyError(f"Missing price data for ticker: {ticker}")

        latest_close = _latest_close(price_cache[cache_key])
        market_value = quantity * latest_close
        total_value += market_value

        by_stock.append(
            {
                "ticker": ticker,
                "quantity": quantity,
                "latest_close": round(latest_close, 2),
                "market_value": round(market_value, 2),
                "allocation_pct": 0.0,
            }
        )

        sector = sector_map.get(ticker, "Unknown")
        by_sector[sector] += market_value

    if total_value == 0:
        raise ValueError("Portfolio total value is zero")

    for item in by_stock:
        item["allocation_pct"] = round((item["market_value"] / total_value) * 100.0, 2)

    sector_rows = [
        {
            "sector": sector,
            "market_value": round(value, 2),
            "allocation_pct": round((value / total_value) * 100.0, 2),
        }
        for sector, value in sorted(by_sector.items())
    ]

    return {
        "total_value": round(total_value, 2),
        "by_stock": by_stock,
        "by_sector": sector_rows,
    }
