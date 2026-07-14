from __future__ import annotations

import unittest

import pandas as pd

from backend.analytics.allocation import compute_portfolio_allocation

_PRICE_CACHE = {
    "RELIANCE.NS": pd.DataFrame(
        {"Close": [100.0, 105.0]},
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    ),
    "TCS.NS": pd.DataFrame(
        {"Close": [200.0, 205.0]},
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    ),
}

_HOLDINGS = [
    {"ticker": "RELIANCE.NS", "quantity": 10},
    {"ticker": "TCS.NS", "quantity": 5},
]

_SECTOR_MAP = {"RELIANCE.NS": "Energy", "TCS.NS": "Technology"}


class AllocationTests(unittest.TestCase):
    def test_total_value_is_correct(self) -> None:
        result = compute_portfolio_allocation(_HOLDINGS, price_cache=_PRICE_CACHE, sector_map=_SECTOR_MAP)

        # 10 * 105 + 5 * 205 = 1050 + 1025 = 2075
        self.assertAlmostEqual(result["total_value"], 2075.0)

    def test_stock_allocation_percentages_sum_to_100(self) -> None:
        result = compute_portfolio_allocation(_HOLDINGS, price_cache=_PRICE_CACHE, sector_map=_SECTOR_MAP)

        total_pct = sum(item["allocation_pct"] for item in result["by_stock"])
        self.assertAlmostEqual(total_pct, 100.0, places=1)

    def test_sector_allocation_percentages_sum_to_100(self) -> None:
        result = compute_portfolio_allocation(_HOLDINGS, price_cache=_PRICE_CACHE, sector_map=_SECTOR_MAP)

        total_pct = sum(item["allocation_pct"] for item in result["by_sector"])
        self.assertAlmostEqual(total_pct, 100.0, places=1)

    def test_stock_grouping_and_values(self) -> None:
        result = compute_portfolio_allocation(_HOLDINGS, price_cache=_PRICE_CACHE, sector_map=_SECTOR_MAP)

        self.assertEqual(result["by_stock"][0]["ticker"], "RELIANCE.NS")
        self.assertAlmostEqual(result["by_stock"][0]["market_value"], 1050.0)
        self.assertAlmostEqual(result["by_stock"][0]["allocation_pct"], 50.6, places=1)

    def test_sector_grouping_and_values(self) -> None:
        result = compute_portfolio_allocation(_HOLDINGS, price_cache=_PRICE_CACHE, sector_map=_SECTOR_MAP)

        sectors = {row["sector"]: row for row in result["by_sector"]}
        self.assertIn("Energy", sectors)
        self.assertIn("Technology", sectors)
        self.assertAlmostEqual(sectors["Energy"]["allocation_pct"], 50.6, places=1)

    def test_unknown_sector_fallback(self) -> None:
        result = compute_portfolio_allocation(_HOLDINGS, price_cache=_PRICE_CACHE, sector_map={})

        sectors = {row["sector"] for row in result["by_sector"]}
        self.assertEqual(sectors, {"Unknown"})

    def test_missing_ticker_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            compute_portfolio_allocation(
                [{"ticker": "MISSING.NS", "quantity": 5}],
                price_cache=_PRICE_CACHE,
            )

    def test_zero_total_value_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            compute_portfolio_allocation(
                [{"ticker": "RELIANCE.NS", "quantity": 0}],
                price_cache=_PRICE_CACHE,
            )

    def test_normalized_cache_key_lookup(self) -> None:
        cache_with_slash = {"A_B": pd.DataFrame({"Close": [50.0, 55.0]}, index=pd.to_datetime(["2024-01-01", "2024-01-02"]))}
        result = compute_portfolio_allocation(
            [{"ticker": "A/B", "quantity": 2}],
            price_cache=cache_with_slash,
        )
        self.assertAlmostEqual(result["total_value"], 110.0)


if __name__ == "__main__":
    unittest.main()
