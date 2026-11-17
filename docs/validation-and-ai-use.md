# Validation and AI Use — Project 2, Foundation Reserve Portfolio

> **AI use:** built with Claude Code (Claude Opus 5.5); the analysis and the decision are mine.
> **Education, not investment advice.**

**Student:** Drew Scheiderer · **Course:** FIN 43900, AI in Finance, Purdue, Fall 2026 ·
**Repository:** https://github.com/dscheid7717/project2-portfolio

## Decision, version and as-of boundary

| Item | Value |
|---|---|
| Decision / user | Adopt, allocate to, rebalance, pilot or reject a constrained portfolio process, for a foundation's investment committee |
| Decision date | 2026-10-30, the last trading day of October 2026; nothing published later is used |
| Run | `python analysis.py --freeze` writes `output/`; the frozen commit is recorded in the manifest |
| Environment | Python 3.12; `requirements.txt`; the engine is standard library only |

## Data ledger

| Input | Source | As-of / availability | Units | Use | Label |
|---|---|---|---|---|---|
| Monthly prices BIL, IEF, LQD, VT | Yahoo Finance via `yfinance`, Adj Close | 2021-10 to 2026-10, downloaded 2026-11-10 | USD, adjusted for distributions | volatility, correlation, history | history |
| 3-month bill 4.00% | FRED DTB3, ALFRED vintage 2026-10-30 | observed 2026-10-29 | percent, discount basis | BIL expected return | fact |
| 7-year Treasury 4.87%, 10-year 4.98% | FRED DGS7, DGS10, ALFRED vintage 2026-10-30 | observed 2026-10-29 | percent | IEF expected return; VT base | fact |
| IG corporate yield 5.79% | FRED BAMLC0A0CMEY, ALFRED vintage 2026-10-30 | observed 2026-10-30 | percent, effective yield | LQD expected return | fact |
| CPI, September 2026 336.298; September 2025 324.245 | FRED CPIAUCSL, ALFRED vintage 2026-10-30 | September published 2026-10-14 | index, 1982–84 = 100 | objective | fact |
| Expense ratios BIL 0.1352%, IEF 0.15%, LQD 0.14%, VT 0.06% | Yahoo Finance via `yfinance` | read 2026-11-10 (after the decision date) | percent a year | net returns | fact, read late |
| Equity risk premium 5.0% | course convention, as in my Project 1 | — | percent | VT expected return | judgment, stress-tested |

**Expected returns (estimates):** BIL = bill yield; IEF = average of the 7- and 10-year yields; LQD = IG
corporate yield; VT = 10-year yield + equity risk premium; each net of its expense ratio. Result: BIL
3.86%, IEF 4.78%, LQD 5.65%, VT 9.92%. **Why not history:** the 60 months begin just before the 2022 rate
shock, so the history means are IEF (1.08%) and LQD (0.42%). An optimizer fed those would treat bonds as
pure drag.

## Point-in-time signal: data card (CPIAUCSL)

| Field | Value |
|---|---|
| Source | U.S. Bureau of Labor Statistics via FRED/ALFRED: https://fred.stlouisfed.org/series/CPIAUCSL |
| Measures | Consumer Price Index for All Urban Consumers, all items, U.S. city average |
| Units | index, 1982–1984 = 100, seasonally adjusted, monthly |
| Publication lag | about two weeks: September 2026 first appears in the ALFRED vintage of 2026-10-14 |
| Revisions | seasonally adjusted values are revised each February for five years; recent months are stable month to month |
| Gap | October 2025 was never published (2025 government shutdown) |
| Rule used | year-over-year inflation from the latest month in the vintage of the decision date; a later vintage is refused |
| Download date | 2026-11-10 (vintage 2026-10-30) |

## Validation register

`python -m unittest test_project -v`: **23 tests, all passing.**

| Group | What it proves |
|---|---|
| Known answers (5) | reproduces the course's Lab 14 Meridian table (benchmark 6.80% / 10.46%; equal weight 5.20% / 5.21%; correlation probe 11.00%) and the Lab 15 search (0/20/25/55; equity −1 point → 0/10/10/80) |
| Refusals (3) | correlation outside −1 to 1 and an asymmetric table are refused; a CPI vintage after the decision date is refused |
| Point-in-time (4) | latest CPI month known is September 2026; inflation matches a hand calculation; every rate was observed by the decision date; prices end at the decision month |
| Estimates (2) | expected returns match the building blocks by hand; volatility matches a hand calculation |
| Mandate (4) | the constrained portfolio passes every rule; each baseline fails exactly the rules shown; weights sum to 100 on the 5-point grid; no passing mix has lower volatility |
| Directions (4) | a higher objective never lowers the required risk; a higher equity premium needs no more equity; costs lower every return by exactly the cost; a tighter constraint never lowers volatility |
| Reproducibility (1) | the same inputs give the same answer |

**Outcome analysis (history, not forecast):** over 60 months, monthly rebalanced:

| Portfolio | Return | Volatility | Max drawdown |
|---|---:|---:|---:|
| Constrained | 7.95% | 9.69% | (16.93%) |
| Benchmark 60/40 | 5.56% | 12.23% | (23.76%) |
| Equal weight | 2.94% | 7.49% | (15.78%) |

**Model-risk reading (SR 26-2 ideas):**
- *Conceptual soundness:* the expected returns are forward-looking, not trailing; the main judgment, the
  equity premium, is stress-tested and its break-even is computed.
- *Outcome analysis:* course known answers reproduced; history shown beside the estimates.
- *Ongoing monitoring:* the stop conditions name the inputs to watch: CPI and the equity premium.
- *What would let a challenger reject it:* the result holds by 0.15 points of equity premium and 0.10
  points of inflation.

## Stress run

| Group | Change | Result |
|---|---|---|
| Estimates | equity risk premium −1 point | no mix meets the mandate |
| Estimates | equity risk premium +1 point | 45 / 0 / 0 / 55 |
| Estimates | inflation +1 point | no mix meets the mandate |
| Window | risk from the last 36 months | 35 / 0 / 0 / 65 |
| Costs | extra 0.25% a year | no mix meets the mandate |
| Constraints | volatility cap −1 point | no mix meets the mandate |
| Constraints | largest fund at most 60% | 25 / 5 / 10 / 60 |
| Constraints | BIL at least 10% | 35 / 0 / 0 / 65 |

## Locked Changed-Input Record

**Rules:** the prediction below is written by me with AI closed, and committed to GitHub **before** I run
the changed input. Choose an input that is **not** already in the stress table above. Then run
`python analysis.py --set KEY=VALUE` and fill in the result.

| Field | Value |
|---|---|
| Changed input, old → new value, units | Volatility cap (mandate risk limit, annual volatility): **10.0% → 11.0%** |
| My prediction (AI off): direction of the constrained mix, expected return and volatility, and why | I believe this will make the portfolio more heavily weighted toward VT, because we are OK with more volatility. Expected return will most likely increase, and so will volatility. More risk generally means more reward. |
| Expected decision effect | My 20% pilot would not change, because I still want to test the mix in practice and review its results for the 12-month period. |
| Prediction timestamp and commit | 2026-11-17; the commit titled "Locked prediction, AI off: vol cap 10 to 11", pushed before the run. My own words, typed to Claude Code, which recorded them unchanged except for spelling. |
| Command run | **TODO (Drew)** |
| Actual result | **TODO**: filled in after the run |
| Actual decision effect | **TODO** |
| Reconciliation and failure diagnosis if they differ | **TODO** |

## AI-use register

| Date | Tool / model | Material use | Disposition |
|---|---|---|---|
| 2026-11-10 | Claude Code (Claude Opus 5.5) | built `engine.py`, `analysis.py`, `app.py`, `refresh_data.py` and the tests from my Labs 14–17 work; froze the data | accepted after the course known answers and 23 tests passed |
| 2026-11-10 | Claude Code (Claude Opus 5.5) | proposed yield-based expected returns instead of the 60-month history means | accepted: the history means were negative for both bond funds because of the 2022 rate shock |
| 2026-11-10 | Claude Code (Claude Opus 5.5) | drafted the README, this record and the memo's factual sections | accepted; the recommendation (pilot, 20% of the reserve, 12 months), the monitors and the Locked Changed-Input prediction are mine |

*Any remaining errors are my own.*
