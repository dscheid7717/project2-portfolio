"""Project 2 analysis: the base run, the stress runs, the allocation range and the stop conditions.

Run:              python analysis.py                  (prints the report)
Freeze output:    python analysis.py --freeze         (runs the tests first; writes output/ only if all pass)
Changed input:    python analysis.py --set erp=4.0    (any BASE_INPUTS key; used for the Locked Changed-Input Record)
"""

import json
import subprocess
import sys
from pathlib import Path

import engine

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"

# Every material input, with its label. `fact` is sourced; `judgment` is mine and is stress-tested.
BASE_INPUTS = {
    "decision_date": "2026-10-30",   # fact: last trading day of October 2026; nothing published later is used
    "erp": 5.0,                      # judgment: equity risk premium over the 10-year Treasury, percent (as in Project 1)
    "real_return_target": 4.0,       # mandate: objective = CPI inflation as known on the decision date + 4%
    "vol_cap": 10.0,                 # mandate: annual volatility at most 10%
    "max_weight": 70.0,              # mandate: no fund above 70%
    "reserve_min": 3.0,              # mandate: at least 3% in BIL for twelve months of payouts
    "window_months": None,           # judgment: risk from all 60 monthly returns
    "risk_regime": "2021-2026",      # judgment: risk from the recent 60 months; "2011-2021" is the regime check
    "extra_cost": 0.0,               # judgment: costs beyond expense ratios, percent a year
    "step": 5,                       # search grid, percentage points
}

# The committee decision: Drew's, recorded 2026-11-17 (docs/decision-memo.md).
COMMITTEE_ACTION = "Pilot the constrained portfolio with 20% of the reserve for 12 months, reviewed quarterly. Stop the pilot and return the sleeve to the current policy if CPI inflation exceeds 3.82% or my equity risk premium falls below 4.85%, since either leaves no mix that can satisfy the mandate. Reconsider adopting if it holds through 4 quarterly reviews with realized volatility under 10%."
COMMITTEE_ACTION_SHORT = "PILOT: 20% of reserve, 12 months"


def pct(value, decimals=2):
    return "not known" if value is None else f"{value:.{decimals}f}%"


def weights_text(weights, tickers):
    return " / ".join(f"{t} {w:.0f}" for t, w in zip(tickers, weights))


def build(inputs):
    data = engine.load_data(inputs)
    base, stress = engine.stress_run(inputs, data)
    erp_floor = engine.breakeven(inputs, "erp", [round(3.0 + 0.05 * i, 2) for i in range(81)], data)
    target_ceiling = None
    for i in range(81):                       # highest real return target (inflation + x) still feasible
        target = round(inputs["real_return_target"] + 0.05 * i, 2)
        if engine.run({**inputs, "real_return_target": target}, data)["feasible"]:
            target_ceiling = target
        else:
            break
    regime = engine.run({**inputs, "risk_regime": "2011-2021"}, data)
    # The load-bearing judgment gets its own range: the constrained mix at each equity risk premium.
    ladder = []
    for erp in [round(4.0 + 0.25 * i, 2) for i in range(9)]:
        case = engine.run({**inputs, "erp": erp}, data)
        mix = case["portfolios"].get("Constrained portfolio")
        ladder.append({"erp": erp, "weights": mix["weights"] if mix else None,
                       "expected_return": mix["expected_return"] if mix else None,
                       "volatility": mix["volatility"] if mix else None})
    return {"base": base, "stress": stress, "range": engine.allocation_range(base, stress),
            "regime": regime, "regime_dates": data["prior_dates"], "erp_ladder": ladder,
            "erp_floor": erp_floor,
            "inflation_ceiling": (base["inflation"] + target_ceiling - inputs["real_return_target"])
            if target_ceiling is not None else None,
            "target_ceiling": target_ceiling}


def report(inputs, built):
    base, tickers = built["base"], built["base"]["tickers"]
    m = base["mandate"]
    lines = [
        "Project 2: Foundation reserve, BIL / IEF / LQD / VT. Education, not investment advice.",
        f"Decision date {inputs['decision_date']}. Prices {base['price_dates'][0]} to {base['price_dates'][1]} "
        f"({base['months']} monthly returns).",
        "",
        "Point-in-time signal: CPI (CPIAUCSL), ALFRED vintage of the decision date",
        f"  Latest month known: {base['cpi_month']}; inflation a year: {base['inflation']:.2f}%",
        f"  Objective = inflation + {inputs['real_return_target']:.1f}% = {m['objective']:.2f}%",
        "",
        "Expected returns (estimates: yields known on the decision date, net of expense ratios)",
    ]
    for t, r, h, v in zip(tickers, base["expected_returns"], base["historical_mean"], base["vols"]):
        lines.append(f"  {t:<4} expected {r:5.2f}%   history mean {h:6.2f}% (not used)   volatility {v:5.2f}%")
    lines += ["", f"Mandate: objective {m['objective']:.2f}%, volatility <= {m['vol_cap']:.1f}%, "
                  f"BIL >= {m['reserve_min']:.1f}%, any fund <= {m['max_weight']:.0f}%", ""]
    for name, p in base["portfolios"].items():
        verdict = "passes every rule" if not p["failed"] else "FAILS: " + "; ".join(p["failed"])
        h = p["history"]
        lines.append(f"{name}: {weights_text(p['weights'], tickers)}")
        lines.append(f"  expected {p['expected_return']:.2f}%, volatility {p['volatility']:.2f}%  ->  {verdict}")
        lines.append(f"  history (monthly rebalanced): {h['annual_return']:.2f}% a year, volatility "
                     f"{h['volatility']:.2f}%, max drawdown {h['max_drawdown']:.2f}%")
    if not base["feasible"]:
        lines.append("Constrained portfolio: no mix meets every mandate rule.")
    lines += ["", "Stress runs (one change each)"]
    for row in built["stress"]:
        mix = weights_text(row["weights"], tickers) if row["weights"] else "no mix meets the mandate"
        moved = "" if row["largest_change"] is None else f"; largest change {row['largest_change']:.0f} points"
        lines.append(f"  [{row['group']}] {row['label']}: {mix}{moved}")
    lines += ["", "Allocation range across the base and the stress runs that still have a mix"]
    if built["range"]:
        lines += [f"  {t}: {lo:.0f}% to {hi:.0f}%" for t, (lo, hi) in built["range"].items()]
    else:
        lines.append("  none: no mix in any case")
    reg = built["regime"]
    reg_mix = reg["portfolios"].get("Constrained portfolio")
    t = reg["tickers"]
    lines += ["", f"Risk regime check (not a stress case): volatility and correlation from "
                  f"{built['regime_dates'][0]} to {built['regime_dates'][1]}, the decade before the rate shock",
              f"  IEF-VT correlation {reg['corr'][t.index('IEF')][t.index('VT')]:.2f} "
              f"(base {base['corr'][t.index('IEF')][t.index('VT')]:.2f}); "
              f"LQD-VT {reg['corr'][t.index('LQD')][t.index('VT')]:.2f} "
              f"(base {base['corr'][t.index('LQD')][t.index('VT')]:.2f})",
              "  " + (f"Constrained portfolio: {weights_text(reg_mix['weights'], t)}, expected "
                      f"{reg_mix['expected_return']:.2f}%, volatility {reg_mix['volatility']:.2f}%"
                      if reg_mix else "no mix meets the mandate")]
    lines += ["", "Equity risk premium range (the load-bearing judgment; base 5.00%)"]
    for row in built["erp_ladder"]:
        mix = (f"{weights_text(row['weights'], tickers)}, expected {row['expected_return']:.2f}%, "
               f"volatility {row['volatility']:.2f}%" if row["weights"] else "no mix meets the mandate")
        lines.append(f"  ERP {row['erp']:.2f}%: {mix}")
    lines += ["", "Stop conditions (computed)",
              f"  Equity risk premium below {pct(built['erp_floor'])}: no mix meets the mandate",
              f"  CPI inflation above {pct(built['inflation_ceiling'])} (objective above "
              f"{pct(None if built['target_ceiling'] is None else base['inflation'] + built['target_ceiling'])}): "
              f"no mix meets the mandate",
              "", f"Committee action: {COMMITTEE_ACTION}"]
    return "\n".join(lines)


def visible_output(inputs, built):
    base = built["base"]
    return {
        "statements": ["AI use: built with Claude Code (Claude Opus 5.5); the analysis and the decision are Drew Scheiderer's.",
                       "Education, not investment advice."],
        "decision_date": inputs["decision_date"],
        "inputs": {k: v for k, v in inputs.items()},
        "point_in_time_signal": {"series": "CPIAUCSL", "latest_month_known": base["cpi_month"],
                                 "inflation_pct": round(base["inflation"], 4)},
        "objective_pct": round(base["mandate"]["objective"], 4),
        "expected_returns_pct": dict(zip(base["tickers"], [round(r, 4) for r in base["expected_returns"]])),
        "volatility_pct": dict(zip(base["tickers"], [round(v, 4) for v in base["vols"]])),
        "portfolios": {name: {"weights_pct": dict(zip(base["tickers"], [round(w, 2) for w in p["weights"]])),
                              "expected_return_pct": round(p["expected_return"], 4),
                              "volatility_pct": round(p["volatility"], 4),
                              "mandate_verdict": "pass" if not p["failed"] else "fail",
                              "failed_rules": p["failed"],
                              "history": {k: round(v, 4) for k, v in p["history"].items()}}
                       for name, p in base["portfolios"].items()},
        "stress": [{**{k: v for k, v in r.items() if k != "weights"},
                    "weights_pct": dict(zip(base["tickers"], r["weights"])) if r["weights"] else None}
                   for r in built["stress"]],
        "allocation_range_pct": built["range"],
        "erp_range": [{"erp_pct": r["erp"],
                       "weights_pct": dict(zip(base["tickers"], r["weights"])) if r["weights"] else None,
                       "volatility_pct": None if r["volatility"] is None else round(r["volatility"], 4)}
                      for r in built["erp_ladder"]],
        "risk_regime_check": {
            "risk_from": list(built["regime_dates"]),
            "correlations": {f"{a}-{b}": round(built["regime"]["corr"][i][j], 4)
                             for i, a in enumerate(base["tickers"]) for j, b in enumerate(base["tickers"]) if i < j},
            "constrained_weights_pct": (dict(zip(base["tickers"], built["regime"]["portfolios"]["Constrained portfolio"]["weights"]))
                                        if built["regime"]["feasible"] else None),
            "volatility_pct": (round(built["regime"]["portfolios"]["Constrained portfolio"]["volatility"], 4)
                               if built["regime"]["feasible"] else None)},
        "stop_conditions": {"erp_below_pct": built["erp_floor"], "inflation_above_pct":
                            None if built["inflation_ceiling"] is None else round(built["inflation_ceiling"], 4)},
        "committee_action": COMMITTEE_ACTION,
        "limitations": [
            "Expected returns are yield-based estimates, not forecasts; the equity risk premium is a judgment.",
            "Volatility and correlation are 60 months of history that include the 2022 rate shock.",
            "LQD's yield is not reduced for expected credit losses.",
            "Expense ratios were read on 2026-11-10, after the decision date; they rarely change.",
        ],
    }


def parse_overrides(args):
    overrides = {}
    for arg in args:
        key, value = arg.split("=", 1)
        if key not in BASE_INPUTS:
            raise SystemExit(f"Unknown input {key}. Choose from: {', '.join(BASE_INPUTS)}")
        overrides[key] = None if value == "None" else type(BASE_INPUTS[key] or 0.0)(value)
    return overrides


def main():
    args = sys.argv[1:]
    freeze = "--freeze" in args
    sets = [a for i, a in enumerate(args) if i > 0 and args[i - 1] == "--set"]
    inputs = {**BASE_INPUTS, **parse_overrides(sets)}
    if freeze:
        if sets:
            raise SystemExit("Refusing to freeze a changed-input run; freeze the base only.")
        tests = subprocess.run([sys.executable, "-m", "unittest", "test_project", "-q"], cwd=HERE)
        if tests.returncode != 0:
            raise SystemExit("Refusing to freeze: a test failed.")
    built = build(inputs)
    text = report(inputs, built)
    print(text)
    if freeze:
        OUTPUT.mkdir(exist_ok=True)
        (OUTPUT / "report.txt").write_text(text + "\n", encoding="utf-8")
        (OUTPUT / "visible_output.json").write_text(json.dumps(visible_output(inputs, built), indent=2),
                                                    encoding="utf-8")
        print(f"\nFroze output/report.txt and output/visible_output.json")


if __name__ == "__main__":
    main()
