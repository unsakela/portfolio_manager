from __future__ import annotations

import math
import unittest

import pandas as pd

from backend.analytics.metrics import compute_beta, compute_max_drawdown, compute_sharpe_ratio, compute_risk_metrics

_DATES = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
_ASSET = pd.Series([100.0, 102.0, 101.0, 103.0, 104.0], index=_DATES)
_BENCHMARK = pd.Series([100.0, 101.0, 100.0, 102.0, 103.0], index=_DATES)


class MetricsTests(unittest.TestCase):
    def test_compute_risk_metrics_returns_expected_fields(self) -> None:
        result = compute_risk_metrics(_ASSET, _BENCHMARK)

        self.assertIn("beta", result)
        self.assertIn("alpha", result)
        self.assertIn("sharpe_ratio", result)
        self.assertIn("max_drawdown_pct", result)

    def test_beta_for_identical_series_is_one(self) -> None:
        result = compute_risk_metrics(_ASSET, _ASSET)

        self.assertAlmostEqual(result["beta"], 1.0, places=4)

    def test_beta_for_uncorrelated_flat_benchmark_is_zero(self) -> None:
        flat = pd.Series([100.0, 100.0, 100.0, 100.0, 100.0], index=_DATES)
        beta = compute_beta(_ASSET, flat)

        self.assertEqual(beta, 0.0)

    def test_beta_is_positive_for_co_moving_series(self) -> None:
        result = compute_risk_metrics(_ASSET, _BENCHMARK)

        self.assertGreater(result["beta"], 0.0)

    def test_sharpe_ratio_positive_for_consistently_rising_prices(self) -> None:
        rising = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0], index=_DATES)
        sharpe = compute_sharpe_ratio(rising)

        self.assertGreater(sharpe, 0.0)

    def test_sharpe_ratio_zero_for_flat_prices(self) -> None:
        flat = pd.Series([100.0, 100.0, 100.0, 100.0, 100.0], index=_DATES)
        sharpe = compute_sharpe_ratio(flat)

        self.assertEqual(sharpe, 0.0)

    def test_max_drawdown_is_non_positive(self) -> None:
        result = compute_risk_metrics(_ASSET, _BENCHMARK)

        self.assertLessEqual(result["max_drawdown_pct"], 0.0)

    def test_max_drawdown_zero_for_monotonically_rising_prices(self) -> None:
        rising = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0], index=_DATES)
        dd = compute_max_drawdown(rising)

        self.assertAlmostEqual(dd, 0.0, places=6)

    def test_max_drawdown_reflects_worst_decline(self) -> None:
        prices = pd.Series([100.0, 120.0, 80.0, 90.0, 110.0], index=_DATES)
        dd = compute_max_drawdown(prices)

        # Peak is 120, trough after peak is 80 → drawdown = (80/120) - 1 = -33.33%
        self.assertAlmostEqual(dd, (80.0 / 120.0 - 1.0) * 100.0, places=4)

    def test_risk_free_rate_is_treated_as_annual(self) -> None:
        rising = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0], index=_DATES)
        sharpe_zero_rf = compute_sharpe_ratio(rising, risk_free_rate=0.0)
        sharpe_high_rf = compute_sharpe_ratio(rising, risk_free_rate=0.10)

        # High annual risk-free rate should lower excess returns → lower Sharpe
        self.assertGreater(sharpe_zero_rf, sharpe_high_rf)

    def test_all_metric_values_are_finite(self) -> None:
        result = compute_risk_metrics(_ASSET, _BENCHMARK)

        for key, value in result.items():
            self.assertTrue(math.isfinite(value), msg=f"{key} is not finite: {value}")


if __name__ == "__main__":
    unittest.main()
