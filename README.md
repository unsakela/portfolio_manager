# Portfolio Risk Analytics

This project is a read-only portfolio analytics app for Indian equities. It uses historical price data only and does not place orders or connect to a broker.

## What is included so far

The first step of the build is now scaffolded:

- a Python backend structure for analytics and simulation
- a data fetcher that pulls historical OHLC data from yfinance
- a local CSV cache layer so the app can work offline after the data is downloaded

## Project structure

```text
backend/
  data/
    cache.py      # local CSV cache helpers
    fetch.py      # downloads and stores historical prices
  analytics/      # planned risk and portfolio metrics modules
  simulation/     # planned Monte Carlo simulation modules
  api/            # planned FastAPI routes
frontend/        # planned React dashboard
data_cache/      # downloaded price data (CSV files)
```

## Setup

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Download historical data:

```bash
python backend/data/fetch.py --tickers RELIANCE.NS ^NSEI ^INDIAVIX
```

This will save the data into the data_cache folder as CSV files.

## Notes

- The data fetcher uses yfinance for historical OHLC data.
- NSE tickers should use the .NS suffix, such as RELIANCE.NS.
- The cache is intentionally simple at this stage so you can test the workflow quickly.

## Next steps

The next modules to implement are:

1. portfolio allocation from holdings and cached prices
2. single-asset Monte Carlo simulation
3. multi-asset Monte Carlo with covariance
4. risk metrics such as beta, alpha, Sharpe, and max drawdown
5. FastAPI endpoints and a React dashboard
