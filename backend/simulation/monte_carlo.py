from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def simulate_gbm(
    price_series: pd.Series | pd.DataFrame,
    horizon_days: int = 252,
    n_paths: int = 1000,
    drift: float | None = None,
    volatility: float | None = None,
    initial_price: float | None = None,
    seed: int | None = None,
) -> Dict[str, Any]:
    """Simulate Geometric Brownian Motion price paths from historical returns."""
    if isinstance(price_series, pd.DataFrame):
        if price_series.empty or "Close" not in price_series.columns:
            raise ValueError("A DataFrame must contain a Close column")
        close = price_series["Close"].dropna()
    else:
        close = price_series.dropna()

    if close.empty:
        raise ValueError("Price series is empty")

    if initial_price is None:
        initial_price = float(close.iloc[-1])

    daily_returns = np.log(close / close.shift(1)).dropna()
    if daily_returns.empty:
        raise ValueError("Could not compute daily returns")

    if drift is None:
        drift = float(daily_returns.mean())
    if volatility is None:
        volatility = float(daily_returns.std(ddof=1))

    if volatility <= 0:
        raise ValueError("Volatility must be positive")

    rng = np.random.default_rng(seed)
    dt = 1.0
    increments = (drift - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * rng.standard_normal((n_paths, horizon_days))
    paths = np.exp(np.cumsum(increments, axis=1)) * initial_price

    last_prices = paths[:, -1]
    losses = np.maximum(0.0, initial_price - last_prices)
    var_95 = float(np.percentile(losses, 95))
    shortfall_mask = losses >= var_95
    expected_shortfall = float(np.mean(losses[shortfall_mask])) if np.any(shortfall_mask) else 0.0
    breach_probability = float(np.mean(last_prices <= initial_price * 0.95))

    return {
        "initial_price": round(float(initial_price), 2),
        "horizon_days": horizon_days,
        "n_paths": n_paths,
        "drift": round(float(drift), 6),
        "volatility": round(float(volatility), 6),
        "simulated_paths": paths.tolist(),
        "var_95": round(float(var_95), 2),
        "expected_shortfall": round(float(expected_shortfall), 2),
        "breach_probability": round(float(breach_probability), 4),
    }
