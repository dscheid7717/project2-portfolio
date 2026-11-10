"""Project 2 validation suite. Run: python -m unittest test_project -v

Known answers come from the course's Lab 14 and Lab 15 Meridian tables; the rest test the mandate,
the point-in-time rule, the estimates and directions of change on my own universe.
"""

import math
import unittest

import analysis
import engine

# Lab 14 Meridian training inputs (course-authored, not market estimates).
M_RET = [3.5, 4.3, 5.0, 8.0]
M_VOL = [0.5, 7.0, 6.0, 16.0]
M_CORR = [[1.00, 0.10, 0.05, 0.00],
          [0.10, 1.00, 0.80, -0.10],
          [0.05, 0.80, 1.00, 0.25],
          [0.00, -0.10, 0.25, 1.00]]
M_TICKERS = ["Bills", "10-year", "IG", "Equity"]
M_MANDATE = {"objective": 6.5, "vol_cap": 100.0, "reserve_min": 3.0, "max_weight": 100.0,
             "reserve_eligible": {"Bills", "10-year"}}


def meridian_cov(corr=M_CORR):
    return engine.covariance_matrix([v / 100 for v in M_VOL], corr)


class KnownAnswers(unittest.TestCase):
    """Lab 14 and Lab 15 known answers, reproduced by this engine."""

    def test_lab14_benchmark(self):
        w = [0, 0, 0.40, 0.60]
        self.assertAlmostEqual(engine.portfolio_return(w, M_RET), 6.80, places=2)
        self.assertAlmostEqual(engine.portfolio_volatility(w, meridian_cov()) * 100, 10.46, places=2)

    def test_lab14_equal_weight(self):
        w = [0.25] * 4
        self.assertAlmostEqual(engine.portfolio_return(w, M_RET), 5.20, places=2)
        self.assertAlmostEqual(engine.portfolio_volatility(w, meridian_cov()) * 100, 5.21, places=2)

    def test_lab14_correlation_probe(self):
        corr = [row[:] for row in M_CORR]
        corr[2][3] = corr[3][2] = 0.50
        self.assertAlmostEqual(engine.portfolio_volatility([0, 0, 0.4, 0.6], meridian_cov(corr)) * 100, 11.00, places=2)

    def test_lab15_search_as_loaded(self):
        best = engine.lowest_risk_mix(M_TICKERS, M_RET, meridian_cov(), M_MANDATE)
        self.assertEqual([round(w * 100) for w in best], [0, 20, 25, 55])

    def test_lab15_equity_one_point_lower(self):
        best = engine.lowest_risk_mix(M_TICKERS, [3.5, 4.3, 5.0, 7.0], meridian_cov(), M_MANDATE)
        self.assertEqual([round(w * 100) for w in best], [0, 10, 10, 80])


class Refusals(unittest.TestCase):
    def test_correlation_out_of_range_refused(self):
        corr = [row[:] for row in M_CORR]
        corr[2][3] = corr[3][2] = 1.3
        with self.assertRaises(ValueError):
            engine.validate_correlation(corr)

    def test_asymmetric_correlation_refused(self):
        corr = [row[:] for row in M_CORR]
        corr[2][3] = 0.30
        with self.assertRaises(ValueError):
            engine.validate_correlation(corr)

    def test_cpi_vintage_after_decision_date_refused(self):
        with self.assertRaises(ValueError):
            engine.cpi_inflation_as_known([("2025-09-01", 324.245), ("2026-09-01", 336.298)],
                                          "2026-11-12", "2026-10-30")


class PointInTime(unittest.TestCase):
    def setUp(self):
        self.data = engine.load_data(analysis.BASE_INPUTS)

    def test_latest_cpi_month_is_september(self):
        # September 2026 CPI was published 2026-10-14; October CPI was not out by 2026-10-30.
        month, _ = engine.cpi_inflation_as_known(self.data["cpi_rows"], self.data["cpi_vintage"], "2026-10-30")
        self.assertEqual(month, "2026-09-01")

    def test_inflation_by_hand(self):
        _, inflation = engine.cpi_inflation_as_known(self.data["cpi_rows"], self.data["cpi_vintage"], "2026-10-30")
        self.assertAlmostEqual(inflation, (336.298 / 324.245 - 1) * 100, places=9)

    def test_rates_observed_by_decision_date(self):
        for series, (obs_date, _) in self.data["rates"].items():
            self.assertLessEqual(obs_date, "2026-10-30", series)

    def test_prices_end_at_decision_month(self):
        self.assertEqual(self.data["dates"][-1], "2026-10-01")
        self.assertEqual(len(self.data["dates"]), 61)


class Estimates(unittest.TestCase):
    def test_expected_returns_building_blocks(self):
        data = engine.load_data(analysis.BASE_INPUTS)
        exp = engine.expected_returns(data["rates"], 5.0, data["expense"])
        self.assertAlmostEqual(exp["BIL"], 4.00 - 0.1352, places=9)
        self.assertAlmostEqual(exp["IEF"], (4.87 + 4.98) / 2 - 0.15, places=9)
        self.assertAlmostEqual(exp["LQD"], 5.79 - 0.14, places=9)
        self.assertAlmostEqual(exp["VT"], 4.98 + 5.0 - 0.06, places=9)

    def test_volatility_by_hand(self):
        returns = [[0.01], [-0.02], [0.03]]
        vols, _ = engine.risk_estimates(returns)
        mean = 0.02 / 3
        sd = math.sqrt(sum((r - mean) ** 2 for r in (0.01, -0.02, 0.03)) / 2)
        self.assertAlmostEqual(vols[0], sd * math.sqrt(12) * 100, places=9)


class Mandate(unittest.TestCase):
    def setUp(self):
        self.result = engine.run(analysis.BASE_INPUTS)

    def test_constrained_portfolio_passes_every_rule(self):
        self.assertTrue(self.result["feasible"])
        self.assertEqual(self.result["portfolios"]["Constrained portfolio"]["failed"], [])

    def test_baselines_fail_their_rules(self):
        p = self.result["portfolios"]
        self.assertEqual(p["Equal weight"]["failed"], ["Expected return meets the objective"])
        self.assertEqual(p["Benchmark 60/40 VT/LQD"]["failed"], ["Volatility within the cap", "Reserve in BIL"])

    def test_weights_sum_and_grid(self):
        w = self.result["portfolios"]["Constrained portfolio"]["weights"]
        self.assertAlmostEqual(sum(w), 100.0, places=9)
        self.assertTrue(all(abs(x / 5 - round(x / 5)) < 1e-9 for x in w))

    def test_search_finds_the_lowest_volatility_passing_mix(self):
        base = self.result
        cov = engine.covariance_matrix([v / 100 for v in base["vols"]], base["corr"])
        best_vol = base["portfolios"]["Constrained portfolio"]["volatility"]
        for w in engine.all_mixes(4, 5):
            r = engine.portfolio_return(w, base["expected_returns"])
            v = engine.portfolio_volatility(w, cov) * 100
            if not engine.failed_rules(engine.mandate_check(w, base["tickers"], r, v, base["mandate"])):
                self.assertGreaterEqual(v, best_vol - 1e-9)


class Directions(unittest.TestCase):
    """The direction each change should move the result, from finance logic, not from the output."""

    def setUp(self):
        self.data = engine.load_data(analysis.BASE_INPUTS)
        self.base = engine.run(analysis.BASE_INPUTS, self.data)

    def test_higher_objective_never_lowers_required_risk(self):
        higher = engine.run({**analysis.BASE_INPUTS, "real_return_target": 4.05}, self.data)
        if higher["feasible"]:
            self.assertGreaterEqual(higher["portfolios"]["Constrained portfolio"]["volatility"],
                                    self.base["portfolios"]["Constrained portfolio"]["volatility"] - 1e-9)

    def test_higher_equity_premium_needs_less_equity(self):
        higher = engine.run({**analysis.BASE_INPUTS, "erp": 6.0}, self.data)
        vt = self.base["tickers"].index("VT")
        self.assertLessEqual(higher["portfolios"]["Constrained portfolio"]["weights"][vt],
                             self.base["portfolios"]["Constrained portfolio"]["weights"][vt])

    def test_costs_lower_every_expected_return(self):
        costly = engine.run({**analysis.BASE_INPUTS, "extra_cost": 0.25}, self.data)
        for a, b in zip(costly["expected_returns"], self.base["expected_returns"]):
            self.assertAlmostEqual(a, b - 0.25, places=9)

    def test_tighter_constraints_never_lower_volatility(self):
        tight = engine.run({**analysis.BASE_INPUTS, "max_weight": 60.0}, self.data)
        if tight["feasible"]:
            self.assertGreaterEqual(tight["portfolios"]["Constrained portfolio"]["volatility"],
                                    self.base["portfolios"]["Constrained portfolio"]["volatility"] - 1e-9)


class Reproducible(unittest.TestCase):
    def test_same_inputs_same_answer(self):
        a = engine.run(analysis.BASE_INPUTS)
        b = engine.run(analysis.BASE_INPUTS)
        self.assertEqual(a["portfolios"]["Constrained portfolio"]["weights"],
                         b["portfolios"]["Constrained portfolio"]["weights"])


if __name__ == "__main__":
    unittest.main()
