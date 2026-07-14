from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def compute_returns(price_series: pd.Series | pd.DataFrame) -> pd.Series:
    if isinstance(price_series, pd.DataFrame):
        if "Close" not in price_series.columns:
            raise ValueError("DataFrame must contain a Close column")
        close = price_series["Close"].dropna()
    else:
        close = price_series.dropna()

    if close.empty:
        raise ValueError("Price series is empty")
    return np.log(close / close.shift(1)).dropna()


def _align_returns(alpha_series: pd.Series, benchmark_series: pd.Series) -> pd.DataFrame:
    alpha_returns = compute_returns(alpha_series)
    benchmark_returns = compute_returns(benchmark_series)
    aligned = pd.concat([alpha_returns, benchmark_returns], axis=1).dropna()
    aligned.columns = ["asset", "benchmark"]
    return aligned


def _beta_from_aligned(aligned: pd.DataFrame) -> float:
    if aligned["benchmark"].std(ddof=1) == 0:
        return 0.0
    covariance = aligned["asset"].cov(aligned["benchmark"])
    variance = aligned["benchmark"].var(ddof=1)
    return float(covariance / variance)


def compute_beta(alpha_series: pd.Series, benchmark_series: pd.Series) -> float:
    return _beta_from_aligned(_align_returns(alpha_series, benchmark_series))


def compute_alpha(alpha_series: pd.Series, benchmark_series: pd.Series, risk_free_rate: float = 0.0) -> float:
    aligned = _align_returns(alpha_series, benchmark_series)
    beta = _beta_from_aligned(aligned)
    daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
    asset_mean = aligned["asset"].mean()
    benchmark_mean = aligned["benchmark"].mean()
    return float((asset_mean - daily_rf) - beta * (benchmark_mean - daily_rf))


def compute_sharpe_ratio(price_series: pd.Series | pd.DataFrame, risk_free_rate: float = 0.0) -> float:
    returns = compute_returns(price_series)
    if returns.empty:
        return 0.0
    daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
    excess = returns - daily_rf
    if excess.std(ddof=1) == 0:
        return 0.0
    return float(excess.mean() / excess.std(ddof=1))


def compute_max_drawdown(price_series: pd.Series | pd.DataFrame) -> float:
    if isinstance(price_series, pd.DataFrame):
        if "Close" not in price_series.columns:
            raise ValueError("DataFrame must contain a Close column")
        close = price_series["Close"].dropna()
    else:
        close = price_series.dropna()

    if close.empty:
        return 0.0
    cumulative_max = close.cummax()
    drawdown = (close / cumulative_max) - 1.0
    return float(drawdown.min() * 100.0)


def compute_risk_metrics(asset_series: pd.Series | pd.DataFrame, benchmark_series: pd.Series | pd.DataFrame, risk_free_rate: float = 0.0) -> Dict[str, Any]:
    return {
        "beta": round(compute_beta(asset_series, benchmark_series), 4),
        "alpha": round(compute_alpha(asset_series, benchmark_series, risk_free_rate=risk_free_rate), 4),
        "sharpe_ratio": round(compute_sharpe_ratio(asset_series, risk_free_rate=risk_free_rate), 4),
        "max_drawdown_pct": round(compute_max_drawdown(asset_series), 4),
    }
