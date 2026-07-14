from __future__ import annotations

from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.analytics.allocation import compute_portfolio_allocation
from backend.analytics.metrics import compute_risk_metrics
from backend.api.cors import add_cors_middleware
from backend.data.cache import load_all_cached_prices, ticker_to_cache_key
from backend.data.fetch import fetch_and_cache
from backend.simulation.monte_carlo import simulate_gbm
from backend.simulation.multi_asset import simulate_multi_asset

app = FastAPI(title="Portfolio Risk Analytics", version="0.1.0")
add_cors_middleware(app)


class HoldingsRequest(BaseModel):
    holdings: List[Dict[str, Any]]
    sector_map: Dict[str, str] | None = None


class MonteCarloRequest(BaseModel):
    ticker: str
    horizon_days: int = 252
    n_paths: int = 1000
    seed: int | None = None


class MultiAssetRequest(BaseModel):
    tickers: List[str]
    weights: Dict[str, float] | None = None
    horizon_days: int = 252
    n_paths: int = 1000
    seed: int | None = None


class MetricsRequest(BaseModel):
    asset_ticker: str
    benchmark_ticker: str
    risk_free_rate: float = 0.0


class FetchRequest(BaseModel):
    tickers: List[str]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/data/fetch")
def fetch_data(request: FetchRequest) -> Dict[str, Any]:
    if not request.tickers:
        return {"status": "error", "message": "No tickers provided"}
    try:
        fetched = fetch_and_cache(request.tickers)
        return {"status": "ok", "fetched": fetched}
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {exc}")


@app.post("/allocation")
def allocation(request: HoldingsRequest) -> Dict[str, Any]:
    try:
        price_cache = load_all_cached_prices()
        return compute_portfolio_allocation(request.holdings, price_cache=price_cache, sector_map=request.sector_map)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/simulation/gbm")
def gbm_simulation(request: MonteCarloRequest) -> Dict[str, Any]:
    price_cache = load_all_cached_prices()
    cache_key = ticker_to_cache_key(request.ticker)
    if cache_key not in price_cache:
        raise HTTPException(status_code=400, detail=f"Missing cached data for {request.ticker}")
    try:
        return simulate_gbm(price_cache[cache_key], horizon_days=request.horizon_days, n_paths=request.n_paths, seed=request.seed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {exc}")


@app.post("/simulation/multi-asset")
def multi_asset_simulation(request: MultiAssetRequest) -> Dict[str, Any]:
    price_cache = load_all_cached_prices()
    missing = [t for t in request.tickers if ticker_to_cache_key(t) not in price_cache]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing cached data for: {', '.join(missing)}")
    price_frames = {ticker: price_cache[ticker_to_cache_key(ticker)] for ticker in request.tickers}
    try:
        return simulate_multi_asset(price_frames, horizon_days=request.horizon_days, n_paths=request.n_paths, weights=request.weights, seed=request.seed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {exc}")


@app.post("/metrics")
def metrics(request: MetricsRequest) -> Dict[str, Any]:
    price_cache = load_all_cached_prices()
    asset_key = ticker_to_cache_key(request.asset_ticker)
    bench_key = ticker_to_cache_key(request.benchmark_ticker)
    if asset_key not in price_cache or bench_key not in price_cache:
        raise HTTPException(status_code=400, detail="Missing cached data for one or both tickers")
    try:
        return compute_risk_metrics(price_cache[asset_key], price_cache[bench_key], risk_free_rate=request.risk_free_rate)
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
