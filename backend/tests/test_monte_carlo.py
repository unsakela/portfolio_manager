from __future__ import annotations

import unittest

import pandas as pd

from backend.simulation.monte_carlo import simulate_gbm

_PRICES = pd.Series(
    [100.0, 102.0, 101.0, 103.0, 104.0],
    index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]),
)


class MonteCarloTests(unittest.TestCase):
    def test_output_shape_and_type(self) -> None:
        result = simulate_gbm(_PRICES, horizon_days=5, n_paths=50, seed=42)

        self.assertEqual(result["horizon_days"], 5)
        self.assertEqual(result["n_paths"], 50)
        self.assertIsInstance(result["simulated_paths"], list)
        self.assertEqual(len(result["simulated_paths"]), 50)
        self.assertEqual(len(result["simulated_paths"][0]), 5)

    def test_risk_metrics_are_non_negative(self) -> None:
        result = simulate_gbm(_PRICES, horizon_days=30, n_paths=500, seed=42)

        self.assertGreaterEqual(result["var_95"], 0.0)
        self.assertGreaterEqual(result["expected_shortfall"], 0.0)
        self.assertGreaterEqual(result["breach_probability"], 0.0)
        self.assertLessEqual(result["breach_probability"], 1.0)

    def test_expected_shortfall_gte_var95(self) -> None:
        result = simulate_gbm(_PRICES, horizon_days=30, n_paths=500, seed=42)

        self.assertGreaterEqual(result["expected_shortfall"], result["var_95"])

    def test_seed_produces_deterministic_output(self) -> None:
        r1 = simulate_gbm(_PRICES, horizon_days=10, n_paths=100, seed=0)
        r2 = simulate_gbm(_PRICES, horizon_days=10, n_paths=100, seed=0)

        self.assertEqual(r1["var_95"], r2["var_95"])
        self.assertEqual(r1["simulated_paths"], r2["simulated_paths"])

    def test_initial_price_matches_last_close(self) -> None:
        result = simulate_gbm(_PRICES, horizon_days=5, n_paths=10, seed=0)

        self.assertAlmostEqual(result["initial_price"], 104.0, places=2)

    def test_dataframe_input_accepted(self) -> None:
        df = pd.DataFrame({"Close": _PRICES.values}, index=_PRICES.index)
        result = simulate_gbm(df, horizon_days=5, n_paths=10, seed=0)

        self.assertIsInstance(result["simulated_paths"], list)


if __name__ == "__main__":
    unittest.main()
