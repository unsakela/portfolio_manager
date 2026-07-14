from __future__ import annotations

import unittest

import pandas as pd

from backend.simulation.multi_asset import simulate_multi_asset

_PRICE_FRAMES = {
    "A": pd.DataFrame(
        {"Close": [100.0, 101.0, 102.0, 103.0, 104.0]},
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]),
    ),
    "B": pd.DataFrame(
        {"Close": [100.0, 102.0, 101.0, 103.0, 105.0]},
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]),
    ),
}


class MultiAssetTests(unittest.TestCase):
    def test_output_shape_and_type(self) -> None:
        result = simulate_multi_asset(_PRICE_FRAMES, horizon_days=5, n_paths=50, weights={"A": 0.6, "B": 0.4}, seed=42)

        self.assertEqual(result["horizon_days"], 5)
        self.assertEqual(result["n_paths"], 50)
        self.assertEqual(result["asset_names"], ["A", "B"])
        self.assertIsInstance(result["portfolio_paths"], list)
        self.assertEqual(len(result["portfolio_paths"]), 50)
        self.assertEqual(len(result["portfolio_paths"][0]), 5)

    def test_covariance_matrix_is_serializable_list(self) -> None:
        result = simulate_multi_asset(_PRICE_FRAMES, horizon_days=5, n_paths=50, seed=42)

        self.assertIsInstance(result["covariance_matrix"], list)
        self.assertEqual(len(result["covariance_matrix"]), 2)
        self.assertEqual(len(result["covariance_matrix"][0]), 2)

    def test_weights_normalised_to_one(self) -> None:
        result = simulate_multi_asset(_PRICE_FRAMES, horizon_days=5, n_paths=50, weights={"A": 3.0, "B": 1.0}, seed=42)

        self.assertAlmostEqual(sum(result["weights"].values()), 1.0, places=4)
        self.assertAlmostEqual(result["weights"]["A"], 0.75, places=4)
        self.assertAlmostEqual(result["weights"]["B"], 0.25, places=4)

    def test_equal_weights_when_none_supplied(self) -> None:
        result = simulate_multi_asset(_PRICE_FRAMES, horizon_days=5, n_paths=50, seed=42)

        self.assertAlmostEqual(result["weights"]["A"], 0.5, places=4)
        self.assertAlmostEqual(result["weights"]["B"], 0.5, places=4)

    def test_risk_metrics_are_non_negative(self) -> None:
        result = simulate_multi_asset(_PRICE_FRAMES, horizon_days=30, n_paths=500, seed=42)

        self.assertGreaterEqual(result["var_95"], 0.0)
        self.assertGreaterEqual(result["expected_shortfall"], 0.0)
        self.assertGreaterEqual(result["breach_probability"], 0.0)
        self.assertLessEqual(result["breach_probability"], 1.0)

    def test_expected_shortfall_gte_var95(self) -> None:
        result = simulate_multi_asset(_PRICE_FRAMES, horizon_days=30, n_paths=500, seed=42)

        self.assertGreaterEqual(result["expected_shortfall"], result["var_95"])

    def test_seed_produces_deterministic_output(self) -> None:
        r1 = simulate_multi_asset(_PRICE_FRAMES, horizon_days=5, n_paths=50, seed=7)
        r2 = simulate_multi_asset(_PRICE_FRAMES, horizon_days=5, n_paths=50, seed=7)

        self.assertEqual(r1["var_95"], r2["var_95"])
        self.assertEqual(r1["portfolio_paths"], r2["portfolio_paths"])


if __name__ == "__main__":
    unittest.main()
