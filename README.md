# Foundation Reserve Portfolio — FIN 43900 Project 2

> **AI use:** built with Claude Code (Claude Opus 5.5), which wrote the code, ran the checks and drafted
> the documentation under my direction. The analysis choices and the committee decision are mine.
> **Education, not investment advice.** This is coursework for FIN 43900, AI in Finance, Purdue, Fall 2026.

**Author:** Drew Scheiderer · **Decision date:** 2026-10-30 · **Universe:** BIL, IEF, LQD, VT

## The decision

A foundation's investment committee asks whether to **adopt, allocate to, rebalance, pilot, or reject** a
constrained portfolio process for its reserve. The mandate:

| Mandate item | Value |
|---|---|
| Objective | expected return at least CPI inflation (as known on the decision date) + 4% → **7.72%** |
| Universe | BIL (T-bills, reserve), IEF (7–10y Treasuries), LQD (IG corporates), VT (global equity) |
| Benchmark | 60% VT / 40% LQD |
| Risk measure and limit | annual volatility at most **10%** |
| Other limits | at least **3% in BIL** (twelve months of payouts); no fund above **70%**; long-only |

## The result (frozen, readable without running anything)

- [`output/report.txt`](output/report.txt): every number, the stress runs, the range and the stop
  conditions.
- [`output/visible_output.json`](output/visible_output.json): the same, machine-readable.
- [`docs/decision-memo.md`](docs/decision-memo.md): the committee memo.
- [`docs/validation-and-ai-use.md`](docs/validation-and-ai-use.md): data ledger, CPI data card, tests,
  Locked Changed-Input Record and AI-use register.

| Portfolio | BIL / IEF / LQD / VT | Expected return | Volatility | Mandate verdict |
|---|---|---:|---:|---|
| Equal weight | 25 / 25 / 25 / 25 | 6.05% | 7.49% | fail: below the objective |
| Benchmark 60/40 | 0 / 0 / 40 / 60 | 8.21% | 12.23% | fail: volatility cap; BIL reserve |
| Constrained portfolio | 35 / 0 / 0 / 65 | 7.80% | 9.69% | pass, by a thin margin |

Four of eight stress runs leave **no mix that meets the mandate**. The process stops if the equity risk
premium falls below **4.85%** or CPI inflation rises above **3.82%**.

**Committee decision:** Pilot the constrained portfolio with 20% of the reserve for 12 months, reviewed quarterly. Stop the pilot and return the sleeve to the current policy if CPI inflation exceeds 3.82% or my equity risk premium falls below 4.85%, since either leaves no mix that can satisfy the mandate. Reconsider adopting if it holds through 4 quarterly reviews with realized volatility under 10%.

## Run it

Python 3.12 and Git. **On Windows, use a short folder path** such as `C:\p2`: in a cold run from a long
path, pip silently skipped part of Streamlit and the app failed with `No module named 'streamlit.proto'`.

**Windows (PowerShell)**, no activation needed:

```
git clone https://github.com/dscheid7717/project2-portfolio C:\p2
cd C:\p2
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

**macOS / Linux:**

```
git clone https://github.com/dscheid7717/project2-portfolio p2 && cd p2
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

The app opens in your browser at http://localhost:8501. Stop it with Ctrl+C. The install can take several
minutes. The result is also readable without running anything, in `output/report.txt`.

Other commands (on Windows, start each with `.venv\Scripts\python` instead of `python`):

| Command | What it does |
|---|---|
| `python analysis.py` | prints the full result (about one second) |
| `python -m unittest test_project -v` | 27 tests: course known answers, refusals, point-in-time, directions, risk regime, ERP range |
| `python analysis.py --freeze` | runs the tests, then rewrites `output/` only if all pass |
| `python analysis.py --set erp=4.0` | one changed input, printed but never frozen (for the Locked Changed-Input Record) |
| `python refresh_data.py` | re-downloads the inputs; not needed, because the frozen data is committed |

No API key, account or `.env` is needed: every input is frozen in `data/`.

## Repository map

| Path | Contents |
|---|---|
| `engine.py` | every calculation: estimates, CPI as known, portfolio math, mandate check, search, history, stress |
| `analysis.py` | the inputs with labels, the report, the frozen output |
| `app.py` | the Streamlit app; renders the engine's results and reruns it from the what-if controls |
| `test_project.py` | validation suite |
| `data/` | frozen inputs: prices (2021–2026, plus 2011–2021 for the risk regime check), ALFRED rates and CPI vintage of 2026-10-30, fund facts |
| `refresh_data.py` | how `data/` was built |
| `docs/` | memo, validation and AI use, video transcripts |
| `project-submission-manifest.csv` | the submission manifest |

## Data sources and point-in-time boundary

Nothing published after **2026-10-30** is used for the decision.

- **Prices:** monthly Adj Close, Yahoo Finance via `yfinance`, 2021-10 to 2026-10 (60 monthly returns).
- **Yields:** FRED series DTB3, DGS7, DGS10 and BAMLC0A0CMEY, from the ALFRED vintage of 2026-10-30.
- **CPI:** CPIAUCSL, ALFRED vintage of 2026-10-30. The latest month known is September 2026, published
  2026-10-14.
- **Expense ratios:** Yahoo Finance via `yfinance`, read 2026-11-10 (after the decision date; they rarely
  change).

## Known limitations

- Expected returns are yield-based **estimates**, and the 5% equity risk premium is a judgment, the same
  course convention as my Project 1. The result depends on it: below 4.85% no mix passes.
- Volatility and correlation are 60 months of history that include the 2022 rate shock; history means
  are shown in the app only to explain why they are not used as expected returns.
- **Why only BIL and VT:** since 2021 bonds have moved with stocks, so the search drops them. With
  2011–2021 risk estimates (the risk regime check), Treasuries hedge stocks and the mix becomes
  BIL 5 / IEF 35 / LQD 0 / VT 60.
- LQD's yield is not reduced for expected credit losses.
- The search uses a 5-point grid, so a finer mix could pass in cases where this one reports none.

*Any remaining errors are my own.*
