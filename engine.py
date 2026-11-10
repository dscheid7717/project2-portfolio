"""Project 2 engine: estimates, portfolio math, the mandate check, the constrained search, stress runs.

Standard library only. Every material number is computed here; analysis.py and app.py only call it.
The portfolio math and search come from my Lab 14-15 portfolio.py; the point-in-time CPI rule comes
from Labs 16-17.
"""

import csv
import math
import statistics
from datetime import date
from pathlib import Path

TOLERANCE = 1e-9
DATA = Path(__file__).resolve().parent / "data"


# ---------------------------------------------------------------- loading the frozen data

def read_prices(path=DATA / "prices.csv"):
    """Monthly Adj Close: (dates, tickers, rows of prices), oldest first."""
    with open(path, newline="") as f:
        rows = [r for r in csv.reader(f) if r]
    tickers = rows[0][1:]
    dates = [r[0] for r in rows[1:]]
    prices = [[float(x) for x in r[1:]] for r in rows[1:]]
    return dates, tickers, prices


def read_rates(path):
    """{series: (observation date, value in percent)} from the frozen ALFRED rates file."""
    with open(path, newline="") as f:
        return {r["series"]: (r["observation_date"], float(r["value_pct"])) for r in csv.DictReader(f)}


def read_cpi_vintage(path):
    """[(month, index)] and the vintage date, from the frozen ALFRED CPI file."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return [(r["month"], float(r["cpi_index"])) for r in rows], rows[-1]["alfred_vintage"]


def read_expense_ratios(path=DATA / "fund_facts.csv"):
    with open(path, newline="") as f:
        return {r["ticker"]: float(r["expense_ratio_pct"]) for r in csv.DictReader(f)}


# ---------------------------------------------------------------- estimates

def monthly_returns(prices):
    """Simple monthly returns from consecutive prices."""
    return [[prices[t][k] / prices[t - 1][k] - 1 for k in range(len(prices[0]))] for t in range(1, len(prices))]


def risk_estimates(returns, last_months=None):
    """Annual volatility (SD x sqrt 12, percent) and correlations from monthly returns. History, not a forecast."""
    if last_months:
        returns = returns[-last_months:]
    columns = list(zip(*returns))
    vols = [statistics.stdev(c) * math.sqrt(12) * 100 for c in columns]
    corr = [[1.0 if i == j else statistics.correlation(columns[i], columns[j])
             for j in range(len(columns))] for i in range(len(columns))]
    return vols, corr


def historical_mean_returns(returns, last_months=None):
    """Mean x 12, percent. Shown only to explain why it is not used as the expected return."""
    if last_months:
        returns = returns[-last_months:]
    return [statistics.mean(c) * 12 * 100 for c in zip(*returns)]


def expected_returns(rates, erp, expense, extra_cost=0.0):
    """Forward-looking expected returns, percent a year, net of expense ratios and any extra cost.

    Building blocks from yields known on the decision date:
      BIL = 3-month bill yield; IEF = average of the 7- and 10-year Treasury yields;
      LQD = ICE BofA US Corporate effective yield; VT = 10-year Treasury yield + equity risk premium.
    """
    gross = {
        "BIL": rates["DTB3"][1],
        "IEF": (rates["DGS7"][1] + rates["DGS10"][1]) / 2,
        "LQD": rates["BAMLC0A0CMEY"][1],
        "VT": rates["DGS10"][1] + erp,
    }
    return {t: gross[t] - expense[t] - extra_cost for t in gross}


def cpi_inflation_as_known(cpi_rows, vintage, decision_date):
    """Year-over-year CPI inflation, percent, from the latest month known on the decision date.

    Point-in-time rule (Labs 16-17): refuse a vintage published after the decision date, and use the
    latest month in that vintage against the same month a year earlier.
    """
    if date.fromisoformat(vintage) > date.fromisoformat(decision_date):
        raise ValueError(f"CPI vintage {vintage} is after the decision date {decision_date}: look-ahead.")
    by_month = dict(cpi_rows)
    latest = max(by_month)
    year_earlier = f"{int(latest[:4]) - 1}{latest[4:]}"
    if year_earlier not in by_month:
        raise ValueError(f"CPI for {year_earlier} is missing from the vintage; inflation is not known.")
    return latest, (by_month[latest] / by_month[year_earlier] - 1) * 100


# ---------------------------------------------------------------- portfolio math (Lab 14)

def validate_correlation(corr):
    """Refuse a correlation table that is not square, symmetric, within [-1, 1], with 1 on the diagonal."""
    n = len(corr)
    for i, row in enumerate(corr):
        if len(row) != n:
            raise ValueError(f"Correlation row {i + 1} has {len(row)} values, expected {n}.")
        for j, value in enumerate(row):
            if not -1.0 - TOLERANCE <= value <= 1.0 + TOLERANCE:
                raise ValueError(f"Correlation ({i + 1},{j + 1}) = {value} is outside -1 to 1.")
            if abs(value - corr[j][i]) > TOLERANCE:
                raise ValueError(f"Correlation table is not symmetric at ({i + 1},{j + 1}).")
        if abs(row[i] - 1.0) > TOLERANCE:
            raise ValueError(f"Diagonal correlation ({i + 1},{i + 1}) must be 1.")


def covariance_matrix(vols, corr):
    """Covariance(i, j) = correlation x vol(i) x vol(j), vols as decimals."""
    return [[corr[i][j] * vols[i] * vols[j] for j in range(len(vols))] for i in range(len(vols))]


def portfolio_return(weights, returns):
    return sum(w * r for w, r in zip(weights, returns))


def portfolio_volatility(weights, cov):
    """sqrt(sum over i, j of w_i w_j cov(i, j)): every correlation term included."""
    n = len(weights)
    return math.sqrt(sum(weights[i] * weights[j] * cov[i][j] for i in range(n) for j in range(n)))


def all_mixes(n_assets, step=5):
    """Every long-only mix in `step`-point increments, as decimal weights summing to 1."""
    units = 100 // step

    def split(remaining, slots):
        if slots == 1:
            yield [remaining]
            return
        for first in range(remaining + 1):
            for rest in split(remaining - first, slots - 1):
                yield [first] + rest

    for mix in split(units, n_assets):
        yield [u * step / 100 for u in mix]


# ---------------------------------------------------------------- the mandate

def mandate_check(weights, tickers, exp_return, vol, mandate):
    """[(rule, measured value, limit text, passed)] for one portfolio. Weights as decimals."""
    reserve = sum(w for w, t in zip(weights, tickers) if t in mandate["reserve_eligible"]) * 100
    largest = max(weights) * 100
    return [
        ("Weights sum to 100%, long-only", sum(weights) * 100,
         "100, none below 0", abs(sum(weights) - 1) <= 1e-6 and min(weights) >= -TOLERANCE),
        ("Expected return meets the objective", exp_return, f">= {mandate['objective']:.2f}%",
         exp_return >= mandate["objective"] - TOLERANCE),
        ("Volatility within the cap", vol, f"<= {mandate['vol_cap']:.1f}%", vol <= mandate["vol_cap"] + TOLERANCE),
        ("Reserve in BIL", reserve, f">= {mandate['reserve_min']:.1f}%", reserve >= mandate["reserve_min"] - TOLERANCE),
        ("Largest single fund", largest, f"<= {mandate['max_weight']:.0f}%", largest <= mandate["max_weight"] + TOLERANCE),
    ]


def failed_rules(checks):
    return [rule for rule, _, _, passed in checks if not passed]


def lowest_risk_mix(tickers, returns, cov, mandate, step=5):
    """Lowest-volatility long-only mix that passes every mandate rule, or None if none does."""
    best, best_vol = None, None
    for weights in all_mixes(len(tickers), step):
        exp_return = portfolio_return(weights, returns)
        if exp_return < mandate["objective"] - TOLERANCE:
            continue
        vol = portfolio_volatility(weights, cov) * 100
        if failed_rules(mandate_check(weights, tickers, exp_return, vol, mandate)):
            continue
        if best_vol is None or vol < best_vol - TOLERANCE:
            best, best_vol = weights, vol
    return best


# ---------------------------------------------------------------- history (outcome analysis)

def realized_history(prices, weights):
    """A fixed mix rebalanced monthly over the price history: annual return and vol (percent), max drawdown."""
    monthly = [sum(w * r for w, r in zip(weights, row)) for row in monthly_returns(prices)]
    value, peak, drawdown = 1.0, 1.0, 0.0
    for r in monthly:
        value *= 1 + r
        peak = max(peak, value)
        drawdown = min(drawdown, value / peak - 1)
    years = len(monthly) / 12
    return {"annual_return": (value ** (1 / years) - 1) * 100,
            "volatility": statistics.stdev(monthly) * math.sqrt(12) * 100,
            "max_drawdown": drawdown * 100}


# ---------------------------------------------------------------- one full run

def run(inputs, data=None):
    """Every result the analysis, the app and the memo use, for one set of inputs."""
    data = data or load_data(inputs)
    tickers, prices = data["tickers"], data["prices"]
    returns = monthly_returns(prices)
    vols, corr = risk_estimates(returns, inputs.get("window_months"))
    validate_correlation(corr)
    cov = covariance_matrix([v / 100 for v in vols], corr)
    exp = expected_returns(data["rates"], inputs["erp"], data["expense"], inputs.get("extra_cost", 0.0))
    exp_list = [exp[t] for t in tickers]
    cpi_month, inflation = cpi_inflation_as_known(data["cpi_rows"], data["cpi_vintage"], inputs["decision_date"])
    mandate = {"objective": inflation + inputs["real_return_target"], "vol_cap": inputs["vol_cap"],
               "reserve_min": inputs["reserve_min"], "max_weight": inputs["max_weight"],
               "reserve_eligible": {"BIL"}}

    candidates = {"Equal weight": [1 / len(tickers)] * len(tickers),
                  "Benchmark 60/40 VT/LQD": [{"VT": 0.60, "LQD": 0.40}.get(t, 0.0) for t in tickers]}
    best = lowest_risk_mix(tickers, exp_list, cov, mandate, inputs.get("step", 5))
    if best is not None:
        candidates["Constrained portfolio"] = best

    portfolios = {}
    for name, weights in candidates.items():
        exp_return = portfolio_return(weights, exp_list)
        vol = portfolio_volatility(weights, cov) * 100
        checks = mandate_check(weights, tickers, exp_return, vol, mandate)
        portfolios[name] = {"weights": [w * 100 for w in weights], "expected_return": exp_return,
                            "volatility": vol, "checks": checks, "failed": failed_rules(checks),
                            "history": realized_history(prices, weights)}
    return {"tickers": tickers, "expected_returns": exp_list, "vols": vols, "corr": corr,
            "historical_mean": historical_mean_returns(returns, inputs.get("window_months")),
            "cpi_month": cpi_month, "inflation": inflation, "mandate": mandate, "portfolios": portfolios,
            "feasible": best is not None, "months": len(returns[-inputs["window_months"]:]
                                                        if inputs.get("window_months") else returns),
            "price_dates": (data["dates"][0], data["dates"][-1])}


def load_data(inputs):
    dates, tickers, prices = read_prices()
    cpi_rows, vintage = read_cpi_vintage(DATA / f"CPIAUCSL_vintage_{inputs['decision_date']}.csv")
    return {"dates": dates, "tickers": tickers, "prices": prices,
            "rates": read_rates(DATA / f"rates_{inputs['decision_date']}.csv"),
            "expense": read_expense_ratios(), "cpi_rows": cpi_rows, "cpi_vintage": vintage}


# ---------------------------------------------------------------- stress runs

def stress_cases(base):
    """(group, label, changed inputs). Each case changes one thing from the base inputs."""
    return [
        ("Estimates", "Equity risk premium 1 point lower", {"erp": base["erp"] - 1}),
        ("Estimates", "Equity risk premium 1 point higher", {"erp": base["erp"] + 1}),
        ("Estimates", "Inflation 1 point higher (objective +1)", {"real_return_target": base["real_return_target"] + 1}),
        ("Window", "Risk from the last 36 months only", {"window_months": 36}),
        ("Costs", "Extra 0.25% a year trading and slippage", {"extra_cost": 0.25}),
        ("Constraints", "Volatility cap 1 point tighter", {"vol_cap": base["vol_cap"] - 1}),
        ("Constraints", "Largest fund at most 60%", {"max_weight": 60}),
        ("Constraints", "BIL reserve at least 10%", {"reserve_min": 10}),
    ]


def stress_run(base, data=None):
    """Each stress case beside the base: the constrained mix, or none, and the largest weight change."""
    data = data or load_data(base)
    base_result = run(base, data)
    base_mix = base_result["portfolios"].get("Constrained portfolio")
    rows = []
    for group, label, change in stress_cases(base):
        result = run({**base, **change}, data)
        mix = result["portfolios"].get("Constrained portfolio")
        moved = None
        if mix and base_mix:
            moved = max(abs(a - b) for a, b in zip(mix["weights"], base_mix["weights"]))
        rows.append({"group": group, "label": label, "change": change,
                     "objective": result["mandate"]["objective"],
                     "weights": mix["weights"] if mix else None,
                     "expected_return": mix["expected_return"] if mix else None,
                     "volatility": mix["volatility"] if mix else None, "largest_change": moved})
    return base_result, rows


def breakeven(base, key, values, data=None):
    """The first value in `values` (scanned in order) at which a mandate-passing mix exists, or None."""
    data = data or load_data(base)
    for value in values:
        if run({**base, key: value}, data)["feasible"]:
            return value
    return None


def allocation_range(base_result, rows):
    """Low and high weight per fund across the base and every stress case that still has a mix."""
    mixes = [base_result["portfolios"]["Constrained portfolio"]["weights"]] if base_result["feasible"] else []
    mixes += [r["weights"] for r in rows if r["weights"]]
    if not mixes:
        return None
    return {t: (min(m[i] for m in mixes), max(m[i] for m in mixes)) for i, t in enumerate(base_result["tickers"])}
