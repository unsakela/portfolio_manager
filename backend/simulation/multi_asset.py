from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping

import numpy as np
import pandas as pd


def simulate_multi_asset(
    price_frames: Mapping[str, pd.DataFrame | pd.Series],
    horizon_days: int = 252,
    n_paths: int = 1000,
    weights: Mapping[str, float] | None = None,
    seed: int | None = None,
) -> Dict[str, Any]:
    """Simulate correlated multi-asset price paths using historical daily returns and a covariance matrix."""
    if not price_frames:
        raise ValueError("At least one price series is required")

    returns_by_asset: list[pd.Series] = []
    asset_names: list[str] = []

    for name, frame in price_frames.items():
        if isinstance(frame, pd.DataFrame):
            if "Close" not in frame.columns:
                raise ValueError(f"{name} must contain a Close column")
            close = frame["Close"].dropna()
        else:
            close = frame.dropna()

        if close.empty:
            raise ValueError(f"No usable price data for {name}")

        returns = np.log(close / close.shift(1)).dropna()
        if returns.empty:
            raise ValueError(f"No returns available for {name}")

        returns_by_asset.append(returns)
        asset_names.append(name)

    aligned_returns = pd.concat(returns_by_asset, axis=1)
    aligned_returns.columns = asset_names
    aligned_returns = aligned_returns.dropna()

    if aligned_returns.empty:
        raise ValueError("No overlapping return data across assets")

    covariance = aligned_returns.cov().to_numpy(dtype=float)
    if np.linalg.matrix_rank(covariance) < len(asset_names):
        covariance = covariance + np.eye(len(asset_names)) * 1e-8

    mean_returns = aligned_returns.mean().to_numpy(dtype=float)

    if weights is None:
        weights = {name: 1.0 / len(asset_names) for name in asset_names}
    weight_vector = np.array([float(weights.get(name, 0.0)) for name in asset_names], dtype=float)
    if np.isclose(weight_vector.sum(), 0.0):
        raise ValueError("Portfolio weights must sum to a non-zero value")
    weight_vector = weight_vector / weight_vector.sum()

    rng = np.random.default_rng(seed)
    chol = np.linalg.cholesky(covariance)
    shocks = rng.standard_normal((n_paths, horizon_days, len(asset_names)))
    correlated = shocks @ chol.T

    drift = mean_returns.reshape(1, 1, -1)
    simulated_returns = drift + correlated

    initial_prices = np.array(
        [
            float(price_frames[name].iloc[-1]["Close"]) if isinstance(price_frames[name], pd.DataFrame) else float(price_frames[name].iloc[-1])
            for name in asset_names
        ],
        dtype=float,
    )
    simulated_prices = np.empty((n_paths, horizon_days, len(asset_names)), dtype=float)
    simulated_prices[:, 0, :] = initial_prices
    for day in range(1, horizon_days):
        simulated_prices[:, day, :] = simulated_prices[:, day - 1, :] * np.exp(simulated_returns[:, day - 1, :])

    portfolio_values = simulated_prices @ weight_vector
    portfolio_initial = float(np.dot(initial_prices, weight_vector))
    portfolio_final = portfolio_values[:, -1]
    losses = np.maximum(0.0, portfolio_initial - portfolio_final)

    var_95_multi = float(np.percentile(losses, 95))
    es_mask = losses >= var_95_multi
    expected_shortfall_multi = float(np.mean(losses[es_mask])) if np.any(es_mask) else 0.0

    return {
        "asset_names": asset_names,
        "weights": {name: round(float(weight_vector[idx]), 4) for idx, name in enumerate(asset_names)},
        "horizon_days": horizon_days,
        "n_paths": n_paths,
        "covariance_matrix": covariance.tolist(),
        "portfolio_paths": portfolio_values.tolist(),
        "var_95": round(var_95_multi, 2),
        "expected_shortfall": round(expected_shortfall_multi, 2),
        "breach_probability": round(float(np.mean(portfolio_final <= portfolio_initial * 0.95)), 4),
    }
