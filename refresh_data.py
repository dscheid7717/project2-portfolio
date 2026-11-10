"""Download and freeze the Project 2 inputs as of the decision date. Not needed to reproduce the result:
the frozen files in data/ are committed. Needs yfinance (pip install yfinance).

Run: python refresh_data.py
"""

import csv
import io
import urllib.request
from datetime import date
from pathlib import Path

DECISION_DATE = "2026-10-30"                 # last trading day of October 2026
TICKERS = ["BIL", "IEF", "LQD", "VT"]
ALFRED_URL = "https://alfred.stlouisfed.org/graph/alfredgraph.csv?id={series}&vintage_date={vintage}"
RATE_SERIES = {
    "DTB3": "3-month Treasury bill, secondary market, discount basis",
    "DGS7": "7-year Treasury constant maturity",
    "DGS10": "10-year Treasury constant maturity",
    "BAMLC0A0CMEY": "ICE BofA US Corporate Index effective yield",
}
DATA = Path(__file__).resolve().parent / "data"


def alfred(series):
    """The series as it read on the decision date (ALFRED vintage): only what was published by then."""
    url = ALFRED_URL.format(series=series, vintage=DECISION_DATE)
    with urllib.request.urlopen(url, timeout=60) as response:
        rows = list(csv.reader(io.StringIO(response.read().decode("utf-8"))))
    return [(d, v) for d, v in rows[1:] if v not in (".", "")]


def main():
    import yfinance as yf

    DATA.mkdir(exist_ok=True)
    prices = yf.download(TICKERS, start="2021-10-01", end="2026-11-01", interval="1mo",
                         auto_adjust=True, progress=False)["Close"][TICKERS]
    with open(DATA / "prices.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date"] + TICKERS)
        for stamp, row in prices.iterrows():
            writer.writerow([stamp.strftime("%Y-%m-%d")] + [f"{v:.4f}" for v in row])

    with open(DATA / f"rates_{DECISION_DATE}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["series", "description", "observation_date", "value_pct", "alfred_vintage"])
        for series, description in RATE_SERIES.items():
            obs_date, value = alfred(series)[-1]
            writer.writerow([series, description, obs_date, value, DECISION_DATE])

    with open(DATA / f"CPIAUCSL_vintage_{DECISION_DATE}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["month", "cpi_index", "alfred_vintage"])
        for month, value in alfred("CPIAUCSL")[-36:]:
            writer.writerow([month, value, DECISION_DATE])

    with open(DATA / "fund_facts.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker", "name", "role", "expense_ratio_pct", "source", "read_on"])
        roles = {"BIL": "Cash and reserve", "IEF": "Government bonds", "LQD": "Investment-grade credit",
                 "VT": "Global equity"}
        for ticker in TICKERS:
            info = yf.Ticker(ticker).info
            writer.writerow([ticker, info.get("longName"), roles[ticker], info.get("netExpenseRatio"),
                             "Yahoo Finance via yfinance", date.today().isoformat()])
    print(f"Froze prices, rates, CPI vintage and fund facts as of {DECISION_DATE} in {DATA}")


if __name__ == "__main__":
    main()
